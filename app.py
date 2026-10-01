# 강민구님
'''
기능 구성
    Flask 서버 (라우팅 / 데이터 바인딩 / 구독자 저장 / 뉴스레터 발송)

화면 구성 (index.html 에 넘기는 데이터)
    1. 실시간 번호 브리핑 카드
       - last_draw           : 지난주 공식 당첨 번호 6개 + 보너스
       - recommended_numbers : 금주의 밸런스 추천 번호 6개
       - recommend_round     : 추천 대상 회차 (지난주 회차 + 1)
    2. 지역구별 1등 명당 랭킹 카드
       - regions / selected_region / stores (Top 3, 카카오맵 링크 포함)
    3. 통계 요약 뱃지
       - hot_numbers / cold_numbers : 최근 30회차 기준 Top 3
    4. 뉴스레터 구독 & 즉시 발송 폼
       - POST /subscribe : 매주 금요일 정기 구독 (subscribers 컬렉션 저장)
       - POST /send-test : 지금 즉시 테스트 전송

실행:
    python app.py  →  http://localhost:5000
    정기 발송 스케줄러까지 켜려면 .env 에 ENABLE_NEWSLETTER_SCHEDULER=1 추가
'''

import os
import threading
import time
from collections import Counter
from datetime import datetime, timedelta, timezone

import schedule
from flask import Flask, render_template, request

# 가짜 데이터: 실제 데이터를 못 가져올 때의 최후 대체값
#   - MOCK_LOTTO_HISTORY  : 회차별 당첨 번호 {round, date, numbers, bonus} 리스트
#   - MOCK_RECOMMENDATION : 추천 결과 {round, recommended_numbers, analysis}
from data.mock_data import MOCK_LOTTO_HISTORY, MOCK_RECOMMENDATION

# 당첨 이력 수집/적재 모듈
#   - get_recent_history(n) : MongoDB lotto_history 컬렉션에서 최신순 n개 회차 조회
#                             반환 형식은 MOCK_LOTTO_HISTORY 와 동일
#   - preprocess()          : data/lotto_history.csv 를 읽어 같은 형식으로 반환 (최신순)
#                             DB 연결이 안 될 때 로컬 CSV 대체용으로 사용
from data_loader import get_recent_history, preprocess

# MongoDB 연결 모듈
#   - get_collection(name) : 컬렉션 객체 반환 (.env 의 MONGO_URI 로 접속)
#   - SUBSCRIBERS          : 뉴스레터 구독자 컬렉션 이름 상수 ("subscribers")
from database import SUBSCRIBERS, get_collection

# 이메일 발송 모듈
#   - send_lotto_email(to_email, recommended_numbers, stores)
#       추천 번호 + 명당 Top 3를 HTML 메일로 만들어 Gmail SMTP 로 발송
#       .env 에 EMAIL_ADDRESS / EMAIL_PASSWORD(Gmail 앱 비밀번호)가 없으면 ValueError
from notifier import send_lotto_email

# 지역구 명당 필터 모듈
#   - load_store_data(path)                     : 판매점 JSON → DataFrame (파일이 없으면 MOCK_STORES)
#   - get_unique_regions(data)                  : 드롭다운용 지역구 목록 (가나다순)
#   - get_top_stores_by_region(region, data)    : 지역구 1등 최다 배출점 Top 3
#       반환 형식: [{rank, store_name, region, win_count, search_url(카카오맵 검색 링크)}]
from store_filter import get_top_stores_by_region, get_unique_regions, load_store_data

# [팀원3] 추천 알고리즘 모듈
#   - generate_recommendation(history_data)
#       당첨 이력의 출현 빈도로 1~45를 Hot(상위15) / Normal(중위15) / Cold(하위15)로 나누고
#       Hot 2개 + Cold 3개 + Normal 1개를 무작위로 뽑아 MOCK_RECOMMENDATION 형식으로 반환
#       {round(최신 회차+1), recommended_numbers, analysis{sum_val, odd_even, hot/cold/normal_count}}
#       history_data 가 없으면 자체적으로 DB → MOCK_LOTTO_HISTORY 순으로 이력을 가져옴
#       ※ 호출할 때마다 결과가 달라지므로(random) 아래 get_recommendation() 에서 회차별로 고정
from recommender import generate_recommendation

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STORES_JSON_PATH = os.path.join(BASE_DIR, "data", "lotto_stores.json")

STATS_ROUNDS = 30          # Hot/Cold 통계 기준 회차 수
STATS_TOP_N = 3            # Hot/Cold 뱃지 개수
NEWSLETTER_TIME = "09:00"  # 매주 금요일 정기 발송 시각 (서버 PC 로컬 시간)

app = Flask(__name__)

# store_filter 의 기본 경로("lotto_stores.json")는 실행 위치 기준이라 파일을 못 찾고
# 가짜 데이터로 대체되므로, 절대 경로로 한 번만 읽어서 재사용한다.
STORE_DATA = load_store_data(STORES_JSON_PATH)


# ------------------------------------------------------------
# 데이터 준비
# ------------------------------------------------------------

def get_history(n=STATS_ROUNDS):
    """최신순 n개 회차 당첨 이력. MongoDB → 로컬 CSV → 가짜 데이터 순으로 시도한다."""
    try:
        history = get_recent_history(n)
        if history:
            return history
    except Exception as e:
        print(f"[app] 당첨 이력 DB 조회 실패, 로컬 CSV 사용: {e}")

    try:
        return preprocess()[:n]
    except Exception as e:
        print(f"[app] 로컬 CSV 읽기 실패, 가짜 데이터 사용: {e}")
        return MOCK_LOTTO_HISTORY[:n]


def get_hot_cold_numbers(history, top_n=STATS_TOP_N):
    """이력에서 가장 많이 나온 Hot / 가장 안 나온 Cold 번호를 뽑는다. (보너스 제외)

    반환: ([{number, count}, ...], [{number, count}, ...])
    출현 횟수가 같으면 작은 번호가 앞에 온다.
    """
    counter = Counter(number for draw in history for number in draw["numbers"])
    counts = [{"number": n, "count": counter.get(n, 0)} for n in range(1, 46)]

    hot = sorted(counts, key=lambda x: (-x["count"], x["number"]))[:top_n]
    cold = sorted(counts, key=lambda x: (x["count"], x["number"]))[:top_n]
    return hot, cold


# 주간 추천 결과를 보관하는 컬렉션. 서버를 재시작해도 그 주 번호가 유지되도록 DB에 저장한다.
#   문서 형식: {period_start: "2026-10-02 09:00", round, recommended_numbers, analysis, created_at}
RECOMMENDATIONS = "recommendations"

# 추천 기간 시작 시각 → 추천 결과. 매 요청마다 DB를 조회하지 않도록 메모리에도 보관한다.
_recommendation_cache = {}


def get_recommend_period_start(now=None):
    """현재 추천 번호가 유효한 기간의 시작 시각 (가장 최근 금요일 NEWSLETTER_TIME)."""
    now = now or datetime.now()
    hour, minute = map(int, NEWSLETTER_TIME.split(":"))

    start = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    start -= timedelta(days=(now.weekday() - 4) % 7)  # 4 = 금요일
    if start > now:  # 금요일인데 아직 발송 시각 전이면 지난주 금요일
        start -= timedelta(days=7)
    return start


def load_saved_recommendation(period_key):
    """DB에 저장된 해당 기간의 추천 결과. 없거나 DB 오류 시 None."""
    try:
        return get_collection(RECOMMENDATIONS).find_one(
            {"period_start": period_key},
            {"_id": 0, "period_start": 0, "created_at": 0},
        )
    except Exception as e:
        print(f"[app] 저장된 추천 번호 조회 실패: {e}")
        return None


def save_recommendation(period_key, recommendation):
    """해당 기간의 추천 결과를 DB에 저장하고, 최종 저장된 결과를 반환한다.

    이미 저장된 결과가 있으면 덮어쓰지 않으므로($setOnInsert),
    여러 요청이 동시에 생성해도 먼저 저장된 하나로 통일된다. DB 오류 시 None.
    """
    try:
        get_collection(RECOMMENDATIONS).update_one(
            {"period_start": period_key},
            {"$setOnInsert": {**recommendation, "created_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
    except Exception as e:
        print(f"[app] 추천 번호 저장 실패 (이번 서버 실행 동안만 유지): {e}")
        return None
    return load_saved_recommendation(period_key)


def get_recommendation(history=None):
    """금주의 밸런스 추천 결과 (MOCK_RECOMMENDATION 형식).

    금요일 NEWSLETTER_TIME 부터 다음 금요일 NEWSLETTER_TIME 전까지 같은 결과를 반환하므로
    화면에 보이는 번호, 테스트 메일, 정기 뉴스레터의 번호가 항상 같다.
    조회 순서: 메모리 → DB 저장본 → 새로 생성 후 DB 저장
    """
    period_key = get_recommend_period_start().strftime("%Y-%m-%d %H:%M")
    if period_key in _recommendation_cache:
        return _recommendation_cache[period_key]

    # 서버 재시작 후에도 이번 주에 이미 뽑아둔 번호가 있으면 그대로 사용
    saved = load_saved_recommendation(period_key)
    if saved:
        _recommendation_cache[period_key] = saved
        return saved

    if history is None:
        history = get_history()
    if not history:
        return MOCK_RECOMMENDATION

    try:
        recommendation = generate_recommendation(history)
    except Exception as e:
        print(f"[app] 추천 번호 생성 실패, 가짜 데이터 사용: {e}")
        return MOCK_RECOMMENDATION

    # DB 저장에 실패하면 메모리에만 보관 (서버 재시작 시 새로 뽑힘)
    _recommendation_cache[period_key] = save_recommendation(period_key, recommendation) or recommendation
    return _recommendation_cache[period_key]


def find_top_stores(region):
    """선택 지역구의 명당 Top 3. 지역이 없으면 빈 리스트."""
    if not region:
        return []
    return get_top_stores_by_region(region, STORE_DATA)


def get_subscriber_region(email):
    """구독자의 선택 지역을 조회한다. 미구독이거나 DB 오류 시 빈 문자열."""
    try:
        subscriber = get_collection(SUBSCRIBERS).find_one({"email": email})
    except Exception as e:
        print(f"[app] 구독자 조회 실패: {e}")
        return ""
    return subscriber.get("region", "") if subscriber else ""


@app.template_filter("ball_color")
def ball_color(number):
    """로또 공식 볼 색상 구간에 맞는 CSS 클래스명을 반환한다.

    템플릿 사용 예: <div class="ball {{ number | ball_color }}">{{ number }}</div>
    """
    number = int(number)
    if number <= 10:
        return "ball-yellow"
    if number <= 20:
        return "ball-blue"
    if number <= 30:
        return "ball-red"
    if number <= 40:
        return "ball-gray"
    return "ball-green"


def render_index(message=None, selected_region=""):
    """모든 라우트가 공통으로 쓰는 메인 화면 렌더링."""
    history = get_history()
    last_draw = history[0] if history else None
    hot_numbers, cold_numbers = get_hot_cold_numbers(history)
    recommendation = get_recommendation(history)

    return render_template(
        "index.html",
        # 1. 실시간 번호 브리핑
        last_draw=last_draw,
        recommended_numbers=recommendation["recommended_numbers"],
        recommend_round=recommendation.get("round"),
        # 2. 지역구별 명당 랭킹
        regions=get_unique_regions(STORE_DATA),
        selected_region=selected_region,
        stores=find_top_stores(selected_region),
        # 3. 통계 요약 뱃지
        stats_rounds=len(history),
        hot_numbers=hot_numbers,
        cold_numbers=cold_numbers,
        # 4. 안내 메시지
        message=message,
    )


# ------------------------------------------------------------
# 라우트
# ------------------------------------------------------------

@app.route("/")
def index():
    return render_index(selected_region=request.args.get("region", "").strip())


@app.route("/subscribe", methods=["POST"])
def subscribe():
    """[매주 금요일 정기 구독] 이메일 + 선호 지역구를 subscribers 컬렉션에 저장."""
    email = request.form.get("email", "").strip().lower()
    region = request.form.get("region", "").strip()

    if not email or not region:
        return render_index(message="이메일과 지역을 모두 입력해주세요.")

    now = datetime.now(timezone.utc)
    try:
        # 같은 이메일로 다시 구독하면 지역만 갱신 (중복 문서 방지)
        get_collection(SUBSCRIBERS).update_one(
            {"email": email},
            {
                "$set": {"region": region, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
    except Exception as e:
        print(f"[app] 구독자 저장 실패: {e}")
        return render_index(
            message="구독 저장에 실패했습니다. DB 연결(.env)을 확인해주세요.",
            selected_region=region,
        )

    return render_index(
        message=f"{email} 님, {region} 지역으로 매주 금요일 뉴스레터가 발송됩니다.",
        selected_region=region,
    )


@app.route("/send-test", methods=["POST"])
def send_test():
    """[⚡ 지금 즉시 테스트 전송] 입력한 이메일로 바로 뉴스레터를 보낸다.

    지역은 폼에서 선택한 값을 우선 쓰고, 없으면 구독 정보에서 찾는다.
    """
    email = request.form.get("email", "").strip().lower()
    region = request.form.get("region", "").strip()

    if not email:
        return render_index(message="받을 이메일 주소를 입력해주세요.")

    if not region:
        region = get_subscriber_region(email)

    try:
        send_lotto_email(
            email,
            get_recommendation()["recommended_numbers"],
            find_top_stores(region),
        )
    except Exception as e:
        print(f"[app] 메일 발송 실패: {e}")
        return render_index(message=f"메일 발송 실패: {e}", selected_region=region)

    message = f"{email} 주소로 테스트 메일을 발송했습니다."
    if not region:
        message += " (지역 정보가 없어 명당 목록은 제외되었습니다.)"
    return render_index(message=message, selected_region=region)


# ------------------------------------------------------------
# 매주 금요일 정기 발송
# ------------------------------------------------------------

def send_newsletter_to_all():
    """전체 구독자에게 각자 선택한 지역 기준으로 뉴스레터를 발송한다. 성공 건수를 반환."""
    try:
        subscribers = list(
            get_collection(SUBSCRIBERS).find({}, {"_id": 0, "email": 1, "region": 1})
        )
    except Exception as e:
        print(f"[newsletter] 구독자 조회 실패: {e}")
        return 0

    numbers = get_recommendation(get_history())["recommended_numbers"]
    sent = 0
    for subscriber in subscribers:
        # 한 명이 실패해도 나머지는 계속 발송
        try:
            send_lotto_email(
                subscriber["email"],
                numbers,
                find_top_stores(subscriber.get("region", "")),
            )
            sent += 1
        except Exception as e:
            print(f"[newsletter] {subscriber.get('email')} 발송 실패: {e}")

    print(f"[newsletter] 정기 발송 완료: {sent}/{len(subscribers)}건")
    return sent


def start_newsletter_scheduler():
    """매주 금요일 NEWSLETTER_TIME 에 send_newsletter_to_all() 을 실행하는 백그라운드 스레드."""
    schedule.every().friday.at(NEWSLETTER_TIME).do(send_newsletter_to_all)

    def run():
        while True:
            schedule.run_pending()
            time.sleep(30)

    threading.Thread(target=run, daemon=True).start()
    print(f"[newsletter] 정기 발송 스케줄러 시작 (매주 금요일 {NEWSLETTER_TIME})")


if __name__ == "__main__":
    # 개발 중 실수로 전체 구독자에게 메일이 가지 않도록 환경변수로 켤 때만 동작.
    # debug 모드는 프로세스가 2개 뜨므로(자동 재시작용) 실제 서버 프로세스에서만 시작한다.
    if os.getenv("ENABLE_NEWSLETTER_SCHEDULER") == "1" and os.getenv("WERKZEUG_RUN_MAIN") == "true":
        start_newsletter_scheduler()

    app.run(debug=True)
