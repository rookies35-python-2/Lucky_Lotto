# 박준영님
import pandas as pd
from urllib.parse import quote

CSV_PATH = "1등당첨현황정보.csv"
JSON_PATH = "lotto_stores.json"


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


if __name__ == "__main__":
    stores = load_and_clean(CSV_PATH)
    print("정제된 매장 수:", len(stores))
    save_json(stores, JSON_PATH)
    print("저장 완료!")
    # TODO: database.py 준비되면 여기서 MongoDB에 적재