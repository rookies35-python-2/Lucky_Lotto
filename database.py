'''
[공통/팀원1] MongoDB Atlas 연결 모듈

[최초 설정] 팀원 모두 한 번만 하면 됩니다.
    1. 프로젝트 루트에 .env 파일을 만들고, 팀원1에게 받은 두 줄을 붙여 넣습니다.
       (형식은 .env.example 참고, DB 사용자: Team2)
    2. 터미널에서 python database.py 를 실행해 "연결 성공"이 나오는지 확인합니다.
    ※ .env는 비밀번호가 들어 있으므로 절대 커밋하지 않습니다. (.gitignore 등록됨)

[사용법] 다른 모듈에서
    from database import get_collection, LOTTO_HISTORY, LOTTO_STORES, SUBSCRIBERS

    history_col = get_collection(LOTTO_HISTORY)
    stores_col = get_collection(LOTTO_STORES)
'''

import os

from dotenv import load_dotenv
from pymongo import MongoClient

# .env 파일에서 접속 정보 읽기
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "lucky_lotto")

# 컬렉션 이름 상수 (오타 방지용, 반드시 이 상수를 사용해주세요)
LOTTO_HISTORY = "lotto_history"   # 팀원 1: 회차별 당첨 번호
LOTTO_STORES = "lotto_stores"     # 팀원 2: 1등 배출 판매점
SUBSCRIBERS = "subscribers"       # 팀원 5: 뉴스레터 구독자

# MongoDB 연결 (수업 방식: client → db → collection)
client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]


def get_client():
    """MongoClient 객체를 반환한다."""
    return client


def get_db():
    """프로젝트 데이터베이스 객체를 반환한다."""
    return db


def get_collection(name):
    """컬렉션 이름을 받아 컬렉션 객체를 반환한다."""
    return db[name]


def ping():
    """DB 연결 여부를 확인한다. 성공 시 True, 실패 시 False."""
    if not MONGO_URI:
        print("[database] MONGO_URI가 설정되지 않았습니다. "
              ".env.example을 참고해 .env 파일을 만들어주세요.")
        return False
    try:
        client.server_info()
        return True
    except Exception as e:
        print(f"[database] MongoDB 연결 실패: {e}")
        return False


if __name__ == "__main__":
    if ping():
        print(f"[database] MongoDB 연결 성공 (DB: {DB_NAME}, 버전: {client.server_info().get('version')})")
        print(f"[database] 현재 컬렉션 목록: {db.list_collection_names()}")