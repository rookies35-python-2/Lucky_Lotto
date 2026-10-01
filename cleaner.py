# 박준영님
import pandas as pd
from urllib.parse import quote
from database import get_collection, LOTTO_STORES

CSV_PATH = "data/1등당첨현황정보.csv"
JSON_PATH = "data/lotto_stores.json"


def load_and_clean(csv_path):
    """CSV를 읽어서 MOCK_STORES 규격으로 정제한 표를 돌려준다."""
    df = pd.read_csv(csv_path, encoding="cp949")
    df.columns = ["seq", "store_name", "region", "win_count"]
    df = df[~df["store_name"].str.contains("인터넷")]
    df = df.drop(columns=["seq"])
    df["search_url"] = "https://map.kakao.com/link/search/" + (df["region"] + " " + df["store_name"]).apply(quote)
    return df


def save_json(df, json_path):
    """정제 결과를 JSON 파일로 저장한다."""
    df.to_json(json_path, orient="records", force_ascii=False, indent=2)


def save_to_db(df):
    """정제 결과를 팀 DB의 lotto_stores 컬렉션에 적재한다."""
    stores_col = get_collection(LOTTO_STORES)
    stores_col.delete_many({})
    stores_col.insert_many(df.to_dict("records"))
    return stores_col.count_documents({})


if __name__ == "__main__":
    stores = load_and_clean(CSV_PATH)
    print("정제된 매장 수:", len(stores))

    save_json(stores, JSON_PATH)
    print("JSON 저장 완료!")

    count = save_to_db(stores)
    print("DB 적재 완료:", count)