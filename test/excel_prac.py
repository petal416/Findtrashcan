import pandas as pd
import requests

from pymongo import MongoClient
import certifi

ca = certifi.where()
client = MongoClient('mongodb+srv://test:sparta@cluster0.72mx2.mongodb.net/Cluster0?retryWrites=true&w=majority',
                     tlsCAFile=ca)
db = client.Findtrashcan

def address_change(address):
    headers = {
        "X-NCP-APIGW-API-KEY-ID": "t1dsmry018",
        "X-NCP-APIGW-API-KEY": "AC6vXWFcIdn3ygmG8fpKiblqm5c34PgMIeeeqIv0"
    }
    # address = "서울시 종로구 사직로 경복궁역 4번출구"
    r = requests.get(f"https://naveropenapi.apigw.ntruss.com/map-geocode/v2/geocode?query={address}", headers=headers)
    response = r.json()
    if response["status"] == "OK":
        if len(response["addresses"]) > 0:
            x = float(response["addresses"][0]["x"])
            y = float(response["addresses"][0]["y"])
            return [x, y]
        else:
            print("좌표를 찾지 못했습니다")
            return 0

def addDB(data):
    for add in data:
        if '일반쓰레기' not in add[3]: continue

        headers = {
            "X-NCP-APIGW-API-KEY-ID": "t1dsmry018",
            "X-NCP-APIGW-API-KEY": "AC6vXWFcIdn3ygmG8fpKiblqm5c34PgMIeeeqIv0"
        }
        gu = add[0]
        ro = add[1]
        detail = str(add[2])
        detail_sujung = detail.strip(ro).strip()
        address = f'서울시 {gu} {ro} {detail_sujung}'

        xy = address_change(address)
        if xy:
            doc = {
                'gu': gu,
                'ro': ro,
                'detail': detail,
                'mapx': xy[0],
                'mapy': xy[1]
            }
            db.trashcan.insert_one(doc)

filename = 'static/서울특별시 가로쓰레기통 현황_202106.xlsx'

df = pd.read_excel(filename, header = 1,
                   names = ['자치구', '도로명', '상세 주소', '수거 쓰레기 종류'],
                   usecols = [2, 3, 4, 6],
                   engine='openpyxl')
df_num = pd.DataFrame.to_numpy(df)

addDB(df_num)