# 유제우님 

# 다른 모듈에서 사용 (팀원 3, 5)
# from data_loader import get_recent_history
# history = get_recent_history(15)   # 최신순 15회, MOCK_LOTTO_HISTORY와 같은 형식


import os
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests
from pymongo import UpdateOne

from database import LOTTO_HISTORY, get_collection, ping

API_URL = "https://www.dhlottery.co.kr/lt645/selectPstLt645InfoNew.do"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
    "Referer": "https://www.dhlottery.co.kr/lt645/result",
}
FIRST_DRAW_DATE = date(2002, 12, 7)   # 1회차 추첨일 (토요일)
KST = timezone(timedelta(hours=9))
REQUEST_DELAY = 1.0                   # 요청 간 대기 시간(초), 서버 부담 및 차단 방지

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "lotto_history.csv")

NUMBER_COLS = ["n1", "n2", "n3", "n4", "n5", "n6"]
CSV_COLS = ["round", "date"] + NUMBER_COLS + ["bonus"]


# ---------------------------------------------------------------
# 1. 수집
# ---------------------------------------------------------------
def estimate_latest_round():
    """오늘 날짜(한국 시간)로 최신 회차를 추정한다. 매주 토요일 1회씩 증가."""
    today = datetime.now(KST).date()
    return (today - FIRST_DRAW_DATE).days // 7 + 1


def fetch_window(round_no, retries=3):
    """round_no 전후 약 10개 회차의 원본 데이터를 받아 리스트로 반환한다."""
    params = {"srchDir": "center", "srchLtEpsd": round_no}
    for attempt in range(1, retries + 1):
        try:
            res = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
            res.raise_for_status()
            if "json" not in res.headers.get("Content-Type", ""):
                raise ValueError("JSON이 아닌 응답 (차단 또는 페이지 이동)")
            data = res.json().get("data") or {}
            return data.get("list") or []
        except (requests.RequestException, ValueError) as e:
            print(f"[수집] {round_no}회 요청 실패 ({attempt}/{retries}): {e}")
            time.sleep(REQUEST_DELAY * 2)
    return []


def collect_recent(n=100):
    """최신 회차부터 역순으로 n개 회차를 수집해 원본 레코드 리스트로 반환한다."""
    collected = {}
    target = estimate_latest_round()
    max_requests = n // 5 + 10

    for _ in range(max_requests):
        items = fetch_window(target)
        for item in items:
            collected[item["ltEpsd"]] = {
                "round": item["ltEpsd"],
                "date": item["ltRflYmd"],
                "n1": item["tm1WnNo"], "n2": item["tm2WnNo"], "n3": item["tm3WnNo"],
                "n4": item["tm4WnNo"], "n5": item["tm5WnNo"], "n6": item["tm6WnNo"],
                "bonus": item["bnsWnNo"],
            }
        print(f"[수집] 기준 {target}회 요청 → {len(items)}건 수신 (누적 {len(collected)}건)")

        if len(collected) >= n:
            break
        # 받은 회차 중 가장 작은 회차의 이전 구간을 다음에 요청
        target = (min(collected) if collected else target) - 5
        if target < 1:
            break
        time.sleep(REQUEST_DELAY)

    latest_rounds = sorted(collected, reverse=True)[:n]
    return [collected[r] for r in latest_rounds]


def save_raw_csv(records, path=CSV_PATH):
    """수집한 원본 레코드를 CSV 파일로 저장한다."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame(records, columns=CSV_COLS).to_csv(path, index=False, encoding="utf-8-sig")
    print(f"[저장] {len(records)}건 → {os.path.relpath(path, BASE_DIR)}")


# ---------------------------------------------------------------
# 2. 전처리
# ---------------------------------------------------------------
def _is_valid(row):
    """번호 6개가 1~45 범위의 서로 다른 수이고, 보너스가 본번호와 겹치지 않는지 검사한다."""
    numbers = [row[c] for c in NUMBER_COLS]
    in_range = all(1 <= x <= 45 for x in numbers + [row["bonus"]])
    return in_range and len(set(numbers)) == 6 and row["bonus"] not in numbers


def preprocess(path=CSV_PATH):
    """CSV를 파싱해 전처리하고 MOCK_LOTTO_HISTORY 형식의 레코드 리스트를 반환한다."""
    df = pd.read_csv(path, dtype={"date": str}, encoding="utf-8-sig")
    total = len(df)

    # (1) 결측치 제거
    df = df.dropna(subset=CSV_COLS)
    missing = total - len(df)

    # (2) 중복 회차 제거
    before = len(df)
    df = df.drop_duplicates(subset="round")
    duplicated = before - len(df)

    # (3) 형식 변환: 정수, 날짜(YYYYMMDD → YYYY-MM-DD)
    df[["round", "bonus"] + NUMBER_COLS] = df[["round", "bonus"] + NUMBER_COLS].astype(int)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d", errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date"])
    bad_date = before - len(df)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # (4) 유효성 검사
    before = len(df)
    df = df[df.apply(_is_valid, axis=1)]
    invalid = before - len(df)

    df = df.sort_values("round", ascending=False)
    records = [
        {
            "round": int(row["round"]),
            "date": row["date"],
            "numbers": sorted(int(row[c]) for c in NUMBER_COLS),
            "bonus": int(row["bonus"]),
        }
        for _, row in df.iterrows()
    ]

    print(
        f"[전처리] 원본 {total}건 → 결측 {missing} / 중복 {duplicated} / "
        f"날짜 오류 {bad_date} / 유효성 오류 {invalid}건 제거 → 최종 {len(records)}건"
    )
    return records


# ---------------------------------------------------------------
# 3. 적재 및 조회
# ---------------------------------------------------------------
def load_to_mongo(records):
    """레코드를 lotto_history 컬렉션에 회차 기준으로 upsert한다. 재실행해도 중복되지 않는다."""
    col = get_collection(LOTTO_HISTORY)
    col.create_index("round", unique=True)
    ops = [UpdateOne({"round": r["round"]}, {"$set": r}, upsert=True) for r in records]
    if not ops:
        print("[적재] 적재할 데이터가 없습니다.")
        return
    result = col.bulk_write(ops)
    print(
        f"[적재] 신규 {result.upserted_count}건 / 갱신 {result.modified_count}건 "
        f"→ 컬렉션 총 {col.count_documents({})}건"
    )


def get_recent_history(n=15):
    """최신순 n개 회차를 MOCK_LOTTO_HISTORY와 같은 형식의 리스트로 반환한다."""
    col = get_collection(LOTTO_HISTORY)
    return list(col.find({}, {"_id": 0}).sort("round", -1).limit(n))


# ---------------------------------------------------------------
# 실행
# ---------------------------------------------------------------
def main(n=100):
    if not ping():
        return
    records = collect_recent(n)
    if not records:
        print("[수집] 데이터를 받지 못했습니다. 네트워크 또는 차단 여부를 확인해주세요.")
        return
    save_raw_csv(records)
    cleaned = preprocess()
    load_to_mongo(cleaned)

    print("[확인] 최신 3회차:")
    for item in get_recent_history(3):
        print(f"  {item}")


if __name__ == "__main__":
    main()