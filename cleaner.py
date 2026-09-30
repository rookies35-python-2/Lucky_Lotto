# 박준영님 
import pandas as pd
from urllib.parse import quote

df = pd.read_csv("1등당첨현황정보.csv", encoding="cp949")

# 1) 열 이름을 영어로 바꾸기
df.columns = ["seq", "store_name", "region", "win_count"]

# 2) 인터넷 판매처 빼기
print("빼기 전:", len(df))
df = df[~df["store_name"].str.contains("인터넷")]
print("빼기 후:", len(df))

# 3) 필요 없는 seq 열 빼기
df = df.drop(columns=["seq"])

# 4) 카카오맵 검색 링크 만들기
df["search_url"] = "https://map.kakao.com/link/search/" + (df["region"] + " " + df["store_name"]).apply(quote)

# 5) 3회 이상 필터가 필요한지 확인용
print("가장 적은 당첨 횟수:", df["win_count"].min())

print(df.head(5).to_string())

# 6) 결과를 JSON 파일로 저장
df.to_json("lotto_stores.json", orient="records", force_ascii=False, indent=2)
print("저장 완료!")