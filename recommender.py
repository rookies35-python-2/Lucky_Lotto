# 김서희님 
import os
import random
from collections import Counter
from pymongo import MongoClient
from dotenv import load_dotenv
from data.mock_data import MOCK_LOTTO_HISTORY

load_dotenv()

# 상수 선언
MIN_NUM = 1
MAX_NUM = 45
LOTTO_COUNT = 6

# ENV 변수 선언
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "lucky_lotto")


def get_history_from_db():
    """MongoDB에서 전체 로또 당첨 이력을 조회합니다."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[DB_NAME]
        
        history = list(db["lotto_history"].find({}, {"_id": 0}))  # id 제외
        return history if history else None
    
    except Exception as e:
        print(f"❌ DB 조회 실패, 목데이터를 반영합니다: {e}")
        return None

def generate_recommendation(history_data=None):
    """
    당첨 이력(history_data)을 Hot/Cold/Normal로 분류 후 
    규칙(Hot 2개, Cold 3개, Normal 1개)에 맞춰 6개 번호와 분석 결과를 반환합니다.
    """
    if not history_data:
        history_data = get_history_from_db()
    if not history_data:
        history_data = MOCK_LOTTO_HISTORY

    # 과거 당첨 번호 수집 및 최신 회차 확인
    all_numbers = []
    latest_round = 0

    for item in history_data:
        nums = item.get("numbers", [])
        all_numbers.extend(nums)
        
        rnd = item.get("round", 0)
        if rnd > latest_round:
            latest_round = rnd

    # 1~45번 전체 번호의 출현 횟수 계산
    counts = Counter(all_numbers)
    for n in range(MIN_NUM, MAX_NUM+1):
        if n not in counts:
            counts[n] = 0

    # 출현 빈도순 정렬 후 Hot / Normal / Cold 그룹 분류 (각 15개)
    sorted_by_frequency = [num for num, _ in counts.most_common()]
    hot_pool = sorted_by_frequency[:15]       # 상위 15개
    normal_pool = sorted_by_frequency[15:30]   # 중위 15개
    cold_pool = sorted_by_frequency[30:]      # 하위 15개

    # 그룹별 번호 추출 (Hot 2개, Cold 3개, Normal 1개 = 총 6개)
    picked_hot = random.sample(hot_pool, 2)
    picked_cold = random.sample(cold_pool, 3)
    picked_normal = random.sample(normal_pool, 1)

    recommended = sorted(picked_hot + picked_cold + picked_normal)

    # 분석 지표 계산
    total_sum = sum(recommended)
    odds = len([n for n in recommended if n % 2 != 0])
    evens = LOTTO_COUNT - odds

    # MOCK_RECOMMENDATION 규격에 맞춘 결과 반환
    return {
        "round": latest_round + 1,
        "recommended_numbers": recommended,
        "analysis": {
            "sum_val": total_sum,
            "odd_even": f"{odds}:{evens}",
            "hot_count": len(picked_hot),
            "cold_count": len(picked_cold),
            "normal_count": len(picked_normal)
        }
    }


# 실행 테스트
if __name__ == "__main__":
    result = generate_recommendation()
    print("=== 추천 로직 테스트 결과 ===")
    print(result)