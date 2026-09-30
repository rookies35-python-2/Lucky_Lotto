'''
팀원1~4가 진짜 데이터를 찾아 가공하기 전까지 사용할 가짜 데이터입니다.

[팀원별 가이드]
- 팀원 1: 동행복권 당첨 이력(최근100회) CSV를 파싱해 MOCK_LOTTO_HISTORY 규격으로 DB에 적재해주세요.
- 팀원 2: 당첨 로또 판매점 CSV를 정제(카카오맵 링크 추가 등)해 MOCK_STORES 규격으로 DB에 적재해주세요.
- 팀원 3: 당첨 이력을 분석해 번호 6개와 분석 결과를 도출하고, MOCK_RECOMMENDATION 형태로 반환하는 함수를 작성해주세요.
- 팀원 4: 사용자의 지역구 입력을 받아 1등 최다 판매점을 정렬하고, MOCK_TOP_STORES 형태로 반환하는 함수를 작성해주세요.
- 팀원 5: 서버(app.py) 라우팅 작성 시 아래 MOCK_RECOMMENDATION, MOCK_TOP_STORES를 임포트해 템플릿으로 전달해주세요.
- 팀원 6: UI(index.html)와 이메일 템플릿(notifier.py) 제작 시 아래 키값(lotto.recommended_numbers, store.store_name 등)을 기준으로 화면과 본문을 구성해주세요.
'''

# 최근 당첨 이력 가짜 데이터
MOCK_LOTTO_HISTORY = [
    {"round": 1139, "date": "2024-09-28", "numbers": [5, 12, 15, 30, 37, 40], "bonus": 18},
    {"round": 1138, "date": "2024-09-21", "numbers": [14, 16, 19, 20, 29, 34], "bonus": 35},
    {"round": 1137, "date": "2024-09-14", "numbers": [4, 9, 12, 15, 33, 45], "bonus": 26},
    {"round": 1136, "date": "2024-09-07", "numbers": [7, 11, 14, 23, 31, 42], "bonus": 38},
    {"round": 1135, "date": "2024-08-31", "numbers": [1, 6, 13, 23, 24, 28], "bonus": 30}
]

# 1등 명당 매장 가짜 데이터
MOCK_STORES = [
    {"store_name": "오케이상사", "region": "서울 서초구", "win_count": 3, "search_url": "https://map.kakao.com/link/search/서울 서초구 오케이상사"},
    {"store_name": "서초방배명당점", "region": "서울 서초구", "win_count": 2, "search_url": "https://map.kakao.com/link/search/서울 서초구 서초방배명당점"},
    {"store_name": "잠실매점", "region": "서울 송파구", "win_count": 5, "search_url": "https://map.kakao.com/link/search/서울 송파구 잠실매점"}
]

# 추천 알고리즘 결과 규격 가짜 데이터
MOCK_RECOMMENDATION = {
    "round": 1140,
    "recommended_numbers": [7, 14, 18, 23, 31, 42],
    "analysis": {"sum_val": 135, "odd_even": "3:3", "hot_count": 2, "cold_count": 3, "normal_count": 1}
}

# 지역구 명당 Top 3 결과 규격 가짜 데이터
MOCK_TOP_STORES = [
    {"rank": 1, "store_name": "오케이상사", "region": "서울 서초구 신반포로", "win_count": 3, "search_url": "https://map.kakao.com/link/search/서울 서초구 오케이상사"},
    {"rank": 2, "store_name": "서초방배명당점", "region": "서울 서초구 방배로", "win_count": 2, "search_url": "https://map.kakao.com/link/search/서울 서초구 서초방배명당점"}
]