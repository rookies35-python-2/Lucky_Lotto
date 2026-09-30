from notifier import send_lotto_email
send_lotto_email(
    "hajihye2003@gmail.com",
    [3, 7, 12, 18, 25, 41],#test numbers
    [{
            "store_name": "행운복권",
            "win_count": 5,
            "region": "서울",
            "search_url": "https://map.naver.com/"
        },
     {
            "store_name": "대박복권",
            "win_count": 4,
            "region": "경기",
            "search_url": "https://map.naver.com/"
        },
      {
            "store_name": "럭키복권",
            "win_count": 3,
            "region": "부산",
            "search_url": "https://map.naver.com/"
        }
    ]   #test stores
)

print("메일 발송 완료")