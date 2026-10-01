'''
[공통/팀원1] MongoDB 연결 모듈

사용법 (다른 팀원):
    from database import get_collection, LOTTO_HISTORY, LOTTO_STORES, SUBSCRIBERS

    history_col = get_collection(LOTTO_HISTORY)
    stores_col = get_collection(LOTTO_STORES)

접속 정보는 프로젝트 루트의 .env 파일에서 읽습니다. (.env.example 참고)
'''

import os

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "lucky_lotto")

# 컬렉션 이름 상수 (오타 방지용, 반드시 이 상수를 사용해주세요)
LOTTO_HISTORY = "lotto_history"   # 팀원 1: 회차별 당첨 번호
LOTTO_STORES = "lotto_stores"     # 팀원 2: 1등 배출 판매점
SUBSCRIBERS = "subscribers"       # 팀원 5: 뉴스레터 구독자

_client = None


def get_client():
    """MongoClient를 한 번만 생성해 재사용한다."""
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    """프로젝트 데이터베이스 객체를 반환한다."""
    return get_client()[DB_NAME]


def get_collection(name):
    """컬렉션 이름을 받아 컬렉션 객체를 반환한다."""
    return get_db()[name]


def ping():
    """DB 연결 여부를 확인한다. 성공 시 True, 실패 시 False."""
    try:
        get_client().admin.command("ping")
        return True
    except Exception as e:
        print(f"[database] MongoDB 연결 실패: {e}")
        return False


if __name__ == "__main__":
    if ping():
        print(f"[database] MongoDB 연결 성공 (DB: {DB_NAME})")
        print(f"[database] 현재 컬렉션 목록: {get_db().list_collection_names()}")