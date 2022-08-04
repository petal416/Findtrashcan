from pymongo import MongoClient
import jwt
import datetime
import hashlib
from flask import Flask, render_template, jsonify, request, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import certifi
import json

app = Flask(__name__)

ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.72mx2.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=ca)
db = client.Findtrashcan
SECRET_KEY = 'SPARTA'


@app.route('/')
def home():
    # DB에 있는 데이터를 읽어서 쓰레기통이 있는 자치구 리스트를 생성
    all_trashcan = list(db.trashcan.find({}, {'_id': False}))
    gu_list = []
    for trashcan in all_trashcan:
        gu_list.append(trashcan['gu'])
    gu_list = list(set(gu_list))

    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload['id']})
        return render_template('index.html', trashcan_list=all_trashcan, gu_list=gu_list,
                               user_info=user_info, msg=None)
    except jwt.ExpiredSignatureError:
        return render_template('index.html', trashcan_list=all_trashcan, gu_list=gu_list,
                               user_info=None, msg="로그인 시간이 만료 되었습니다.")
    except jwt.exceptions.DecodeError:
        return render_template('index.html', trashcan_list=all_trashcan, gu_list=gu_list,
                               user_info=None, msg=None)



@app.route('/login')
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


# 로그인 서버
# 클라이언트 -> 서버 검증요청 -> ID, PW 존재 여부 확인
@app.route('/sign_in', methods=['POST'])
def sign_in():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    # PW 암호화
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    # ID, PW 존재 여부 확인
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})

    # ID, PW 매칭 여부 확인
    if result is not None:
        payload = {
         'id': username_receive,
         'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        # JWT 토큰 발행
        # .decode('utf-8')삭제 -> 이미 decode가 됐기 때문에 decode 할게 없음
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        # JWT 토큰 -> 클라이언트로 발행
        return jsonify({'result': 'success', 'token': token})
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 회원가입 서버
@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,                               # 아이디
        "password": password_hash,                                  # 비밀번호
        "nickname": nickname_receive,                               # 닉네임
        "profile_pic": "",                                          # 프로필 사진 파일 이름
        "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        "profile_info": ""                                          # 프로필 한 마디
    }
    # ID, PW 서버로 저장
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


# ID 중복확인
@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    # DB에서 username을 받는다.
    username_receive = request.form['username_give']
    # DB에서 username이 받아지면 exist(이미존재함), bool(False)를 의미
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# 프로필 수정 서버
@app.route('/update_profile', methods=['POST'])
def save_img():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        username = payload["id"]
        name_receive = request.form["name_give"]
        about_receive = request.form["about_give"]
        password_receive = request.form["password_give"]
        pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
        new_doc = {
            "nickname": name_receive,
            "profile_info": about_receive,
            "password": pw_hash
        }
        if 'file_give' in request.files:
            file = request.files["file_give"]
            filename = secure_filename(file.filename)
            extension = filename.split(".")[-1]
            file_path = f"profile_pics/{username}.{extension}"
            file.save("./static/"+file_path)
            new_doc["profile_pic"] = filename
            new_doc["profile_pic_real"] = file_path
        db.users.update_one({'username': payload['id']}, {'$set':new_doc})
        return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



@app.route("/detail/<address>")
def detailInfo(address):
    address_list = address.split(' ')
    gu = address_list[0]
    ro = address_list[1]
    detail = address_list[2:]
    detail_adv = ''
    for det in detail:
        detail_adv += (det + ' ')
    detail_adv = detail_adv.strip(' ')

    query = {'$and': [{'gu': gu}, {'ro': ro}, {'detail': detail_adv}]}
    data = db.trashcan.find_one(query, {'_id': False})

    return render_template("detail.html", address=address, data=json.dumps(data))


# 프로필 페이지 서버
@app.route('/user/<username>')
def user(username):
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (username == payload["id"])    # 내 프로필이면 True, 다른 사람 프로필 페이지면 False

        user_info = db.users.find_one({"username": username}, {"_id": False})
        return render_template('user.html', user_info=user_info, status=status)
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 리뷰 추가
@app.route('/reviewing', methods=['POST'])
def add_review():
    token_receive = request.cookies.get('mytoken')

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        trashcan_receive = request.form["trashcan_give"]
        star_receive = request.form["star_give"]
        review_receive = request.form["review_give"]
        date_receive = request.form["date_give"]

        doc = {
            "username": user_info["username"],
            "trashcan": trashcan_receive,
            "star": star_receive,
            "review": review_receive,
            "date": date_receive
        }

        db.reviews.insert_one(doc)

        return jsonify({'result': 'success', 'msg': '리뷰 등록 성공'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'result': 'fail', 'msg': '로그인 후 이용 가능 합니다!'})


# 해당 유저가 남긴 쓰레기통들에 대한 리뷰 가져오기
@app.route("/get_reviews", methods=['GET'])
def get_reviews_user():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        my_username = payload["id"]
        username_receive = request.args.get("username_give")

        if username_receive == "":
            reviews = list(db.reviews.find({}).sort("date", -1).limit(20))
        else:
            reviews = list(db.reviews.find({"username": username_receive}).sort("date", -1).limit(20))

            for review in reviews:
                review["_id"] = str(review["_id"])

        return jsonify({"result": "success", "reviews": reviews})
    except(jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))


# 해당 주소의 쓰레기통에 대한 리뷰 가져오기
@app.route("/get_trashcan_reviews", methods=['GET'])
def get_reviews_trashcan():
    trashcan_receive = request.args.get("trashcan_give")
    print(trashcan_receive)

    trashcan_reviews = list(db.reviews.find({"trashcan": trashcan_receive}).sort("date", -1).limit(20))

    for review in trashcan_reviews:
        review["_id"] = str(review["_id"])

    return jsonify({"result": "success", "reviews": trashcan_reviews})


@app.route("", methods=['POST'])
def update_favorite():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({"username": payload["id"]})
        trashcan_receive = request.form["trashcan_give"]
        type_receive = request.form["type_give"]
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
