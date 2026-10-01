# 강민구님
'''
[팀원5] Flask 서버 (라우팅 / 구독자 저장 / 테스트 메일 발송)

실행:
    python app.py  →  http://localhost:5000
'''

from datetime import datetime, timezone

from flask import Flask, render_template, request

from data.mock_data import MOCK_RECOMMENDATION
from database import SUBSCRIBERS, get_collection
from notifier import send_lotto_email
from store_filter import get_top_stores_by_region, get_unique_regions

app = Flask(__name__)


def get_recommendation():
    """이번 주 추천 번호 6개를 반환한다."""
    # TODO: 팀원3의 recommender.py가 완성되면 실제 추천 함수 호출로 교체
    #   예) from recommender import recommend_numbers
    #       return recommend_numbers()["recommended_numbers"]
    return MOCK_RECOMMENDATION["recommended_numbers"]


def get_subscriber_region(email):
    """구독자의 선택 지역을 조회한다. 미구독이거나 DB 오류 시 빈 문자열."""
    try:
        subscriber = get_collection(SUBSCRIBERS).find_one({"email": email})
    except Exception as e:
        print(f"[app] 구독자 조회 실패: {e}")
        return ""
    return subscriber.get("region", "") if subscriber else ""


def render_index(message=None, selected_region=""):
    """모든 라우트가 공통으로 쓰는 메인 화면 렌더링."""
    stores = get_top_stores_by_region(selected_region) if selected_region else []
    return render_template(
        "index.html",
        recommended_numbers=get_recommendation(),
        regions=get_unique_regions(),
        selected_region=selected_region,
        stores=stores,
        message=message,
    )


@app.route("/")
def index():
    return render_index(selected_region=request.args.get("region", "").strip())


@app.route("/subscribe", methods=["POST"])
def subscribe():
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
        message=f"{email} 님, {region} 지역으로 구독되었습니다.",
        selected_region=region,
    )


@app.route("/send-test", methods=["POST"])
def send_test():
    email = request.form.get("email", "").strip().lower()

    if not email:
        return render_index(message="받을 이메일 주소를 입력해주세요.")

    # 폼에 지역 입력이 없으므로 구독 정보에서 지역을 가져온다
    region = get_subscriber_region(email)
    stores = get_top_stores_by_region(region) if region else []

    try:
        send_lotto_email(email, get_recommendation(), stores)
    except Exception as e:
        print(f"[app] 메일 발송 실패: {e}")
        return render_index(message=f"메일 발송 실패: {e}", selected_region=region)

    message = f"{email} 주소로 테스트 메일을 발송했습니다."
    if not region:
        message += " (구독 정보가 없어 명당 목록은 제외되었습니다.)"
    return render_index(message=message, selected_region=region)


def send_newsletter_to_all():
    """전체 구독자에게 각자 선택한 지역 기준으로 뉴스레터를 발송한다."""
    # TODO: 정기 발송(schedule) 연동 시 구현
    #   1. get_collection(SUBSCRIBERS).find() 로 구독자 전체 조회
    #   2. 구독자별 get_top_stores_by_region(region) 조회
    #   3. send_lotto_email(email, get_recommendation(), stores) 호출
    #   4. 한 명 실패해도 나머지는 계속 발송되도록 개별 try/except
    raise NotImplementedError


if __name__ == "__main__":
    app.run(debug=True)
