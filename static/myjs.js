function get_reviews(username) {
    if (username === undefined) {
        username = ""
    }
    $("#review-box").empty()

    $.ajax({
        type: "GET",
        url: `/get_reviews?username_give=${username}`,
        data: {},
        success: function (response) {
            let reviews = response["reviews"]

            for (let i = 0; i < reviews.length; i++) {
                let review = reviews[i]
                let time_review = new Date(review["date"])
                let time_text = time_to_str(time_review)

                let temp_html = ``
                temp_html = `<div class="box" id="${review["_id"]}">
                                        <div class="columns">
                                            <div class="column is-4">${review['username']}</div>
                                            <div class="column is-4">${review['star']}</div>
                                            <div class="column is-4">${time_text}</div>
                                        </div>
                                        <div class="columns">
                                            <div class="column is-full">
                                            <p>{쓰레기통 정보(위치)}</p>
                                            </div>
                                        </div>
                                        <div class="columns">
                                            <div class="column is-full"><p>${review['review']}</p></div>
                                        </div>
                                     </div>`

                $("#review-box").append(temp_html)

            }

        }
    })
}

function logout() {
    $.removeCookie('mytoken');
    alert('로그아웃!')
    window.location.href = '/'
}