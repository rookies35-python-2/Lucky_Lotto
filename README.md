# 🍀 Lucky Lotto (로또 번호 추천 & 1등 명당 안내 서비스)

> **공공데이터와 역대 당첨 이력을 활용한 통계 기반 로또 번호 추천 및 명당 판매점 안내 웹 서비스**

본 프로젝트는 동행복권 공식 데이터와 공공데이터포털의 1등 배출점 데이터를 수집·가공하여 **MongoDB**에 적재하고, 빈도 기반 알고리즘을 통해 번호를 추천하는 데이터 파이프라인 기반 웹 애플리케이션입니다.

---
<br>

## 📌 1. 프로젝트 개요

* **서비스 목적:** 단순 난수 추첨을 넘어 역대 출현 통계를 반영한 번호 조합과 주변 1등 당첨 명당 판매점 정보를 직관적인 대시보드와 정기 이메일로 제공합니다.
* **주요 타깃:** 통계적 근거를 바탕으로 번호를 조합하고 주변 명당 판매점을 찾고자 하는 사용자.

---
<br>

## 🛠️ 2. 기술 스택 (Tech Stack)

| 역할 | 도구 |
| :--- | :--- |
| **Backend & Web** | <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=Python&logoColor=white"> <img src="https://img.shields.io/badge/Flask-000000?style=flat-square&logo=Flask&logoColor=white"> <img src="https://img.shields.io/badge/Jinja2-B41717?style=flat-square&logo=Jinja&logoColor=white"> <img src="https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=HTML5&logoColor=white"> <img src="https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=CSS3&logoColor=white"> |
| **Data & Pipeline** | <img src="https://img.shields.io/badge/Pandas-150458?style=flat-square&logo=Pandas&logoColor=white"> <img src="https://img.shields.io/badge/MongoDB-47A248?style=flat-square&logo=MongoDB&logoColor=white"> <img src="https://img.shields.io/badge/공공데이터포털_CSV-003668?style=flat-square&logoColor=white"> <img src="https://img.shields.io/badge/동행복권_API-005BAC?style=flat-square&logoColor=white"> |
| **Automation & Mail** | <img src="https://img.shields.io/badge/schedule-00599C?style=flat-square&logoColor=white"> <img src="https://img.shields.io/badge/Gmail_SMTP-EA4335?style=flat-square&logo=Gmail&logoColor=white"> |
| **DevOps & Tools** | <img src="https://img.shields.io/badge/VS_Code-007ACC?style=flat-square&logo=Visual-Studio-Code&logoColor=white"> <img src="https://img.shields.io/badge/Git-F05032?style=flat-square&logo=Git&logoColor=white"> <img src="https://img.shields.io/badge/GitHub-181717?style=flat-square&logo=GitHub&logoColor=white"> |

---
<br>

## 🏗️ 3. 시스템 아키텍처 & 데이터 파이프라인

```text
[동행복권 당첨 이력] ─── (pandas 전처리) ───┐
                                          ├───▶ [ MongoDB 적재 ]
[공공데이터 1등 판매점] ── (pandas 전처리) ───┘        ├─ lotto_history 컬렉션
                                                      ├─ lotto_stores 컬렉션
                                                      └─ subscribers 컬렉션
                                                                │
                 ┌──────────────────────────────────────────────┘
                 ▼                                              ▼
   [추천 엔진 (recommender.py)]                   [정기 발송 (scheduler)]
    - 빈도 통계(Hot/Cold/Normal)                    - schedule + smtplib
    - 홀짝/총합 분석                                - 구독자 정기 이메일 발송
                 │
                 ▼
   [Flask 웹 애플리케이션 대시보드]
    - 로또 볼 UI 인터페이스
    - 카카오맵 링크 연동
```

---
<br>

## 📊 4. 데이터 파이프라인 상세

| 구분 | 내용 |
| :--- | :--- |
| **데이터 수집** | • **로또 역대 당첨 번호 데이터**: [동행복권 공식 홈페이지](https://www.dhlottery.co.kr/lt645/result)<br>• **전국 로또 1등 당첨 판매점 데이터**: [공공데이터포털](https://www.data.go.kr/data/15059963/fileData.do) |
| **전처리 및 정제** | • `pandas`를 이용한 결측치 제거, 데이터 타입 캐스팅, 불필요 필드 정제<br>• 주소 데이터 정규화 및 회차별 번호 배열 구조화 |
| **저장소** | • **MongoDB** (`lucky_lotto` 데이터베이스)<br>&nbsp;&nbsp;- `lotto_history`: 회차별 당첨 번호 및 보너스 번호<br>&nbsp;&nbsp;- `lotto_stores`: 1등 배출 판매점 상호명, 주소, 좌표<br>&nbsp;&nbsp;- `subscribers`: 뉴스레터 구독자 이메일 관리<br>• DB 미연동 시 서비스 중단을 방지하는 **Fallback 목데이터(Mock Data)** 구축 |
| **시각화 & UI** | • **Flask & Jinja2**: 서버 사이드 렌더링 기반 대시보드<br>• **CSS 인터페이스**: 번호 대역별 고유 색상을 적용한 직관적인 볼(Ball) UI<br>• **카카오맵 연동**: 매장 위치 바로가기 연동을 통한 지리적 가독성 확보 |
| **출력 및 제공** | • **Flask Web Dashboard**: 실시간 추천 번호 및 분석 지표 렌더링<br>• **자동화 알림**: `schedule`과 `smtplib`를 활용 매주 추천 번호 이메일 발송 |

---
<br>

## ⚙️ 5. 추천 알고리즘 로직 (`recommender.py`)

1. **빈도 분석**: 역대 전 회차 당첨 번호를 집계(`Counter`)하여 1~45번의 출현 빈도수 전수 계산.
2. **풀(Pool) 분할 (각 15개)**:
   * **Hot (상위 15개)**: 역대 출현 빈도가 가장 높은 다빈도 번호군
   * **Normal (중위 15개)**: 평균적인 출현 빈도를 유지하는 번호군
   * **Cold (하위 15개)**: 상대적으로 출현 빈도가 낮았던 미출현/소외 번호군
3. **가중 샘플링 (2 : 3 : 1 전략)**:
   * 단순 완전 무작위 추출을 지양하고, **Hot 2개 + Cold 3개 + Normal 1개** 조합을 구성하여 통계적 균형을 유지.
4. **통계 기반 유효 번호 검증 (총합 정규분포 필터링)**:
   * **총합(Sum) 유효 구간 검증 (`100 <= sum_val <= 175`)**: 

---
<br>

## 💡 6. 데이터 분석 인사이트 및 결과 해석

### 1. 출현 빈도 불균형과 회귀 경향 (Hot 2 : Cold 3 : Normal 1)
* **데이터 발견:** 역대 전 회차(1,200회 이상) 데이터를 전수 집계한 결과, 이론상 모든 번호의 당첨 확률은 동일(1/45)함에도 장기 통계상 번호별 출현 편차가 관측되었습니다.
* **로직 적용:** 최근 흐름상 연속 등장하는 번호군(Hot)과 장기적 평균 빈도로 회귀하려는 미출현 번호군(Cold)을 고르게 조합하여 통계적 다양성을 확보했습니다.

### 2. 번호 총합의 정규분포 유효 구간 검증 (`sum_val`)
* **데이터 발견:** 1~45 중 6개 번호를 무작위 추출할 때 이론적 기대 평균 합은 약 138입니다. 역대 실제 1등 당첨 번호의 70% 이상이 정규분포 1시그마 내외인 **100 ~ 175 구간**에 집중되어 있음을 확인했습니다.
* **로직 적용:** 추출된 조합의 총합을 실시간 산출하여 역대 당첨 데이터의 유효 밀집 구간 내에 속하는지 검증 지표로 제공합니다.

### 3. 1등 배출 명당 판매점의 지리적 집중도와 실용 가치
* **데이터 발견:** 공공데이터 분석 결과, 유동 인구가 집중된 교통 요충지 및 주요 상권 매장에 1등 당첨 이력이 편중되는 현상을 확인했습니다.
* **서비스 가치:** 이는 당첨 확률 자체의 차이보다는 총 판매량 비례에 기인한 현상이지만, 사용자에게는 높은 심리적 신뢰도를 제공하므로 **카카오맵 연동**을 통해 실제 방문 접근성을 높였습니다.

---
<br>

## 📁 7. 프로젝트 디렉토리 구조

```text
├── data/                    # 원본 CSV 데이터 및 목데이터 관리
├── templates/               # 프론트엔드 UI 화면
│   └── index.html           # 대시보드 메인 페이지
├── .env.example             # 환경 변수 설정 예시 파일
├── .gitignore               # Git 추적 제외 목록
├── app.py                   # Flask 웹 애플리케이션 및 라우팅
├── cleaner.py               # 1등 당첨 판매점 데이터 정제 및 DB 적재
├── data_loader.py           # 동행복권 당첨 이력 전처리 및 DB 적재
├── database.py              # MongoDB 싱글톤 연결 및 컬렉션 공통 모듈
├── notifier.py              # Gmail SMTP 연동 이메일 발송 모듈
├── recommender.py           # Hot/Cold/Normal 기반 로또 번호 추천 엔진
├── store_filter.py          # 지역구 기준 1등 배출점 필터링 및 랭킹 엔진
├── requirements.txt         # 프로젝트 의존성 라이브러리 목록
└── README.md                # 프로젝트 안내 문서
```

---
<br>

## 🚀 8. 시작하기 (Getting Started)

### 1) 환경 설정 및 패키지 설치
가상환경 생성 및 활성화:
* Windows: `python -m venv venv` 후 `venv\Scripts\activate`
* Mac/Linux: `python -m venv venv` 후 `source venv/bin/activate`

의존성 설치:
* `pip install -r requirements.txt`

### 2) 환경 변수 설정 (`.env`)
프로젝트 루트 경로에 `.env` 파일을 생성하고 데이터베이스 정보를 입력합니다.
* `MONGO_URI=mongodb://localhost:27017`
* `DB_NAME=lucky_lotto`
* `EMAIL_ADDRESS=your_email@gmail.com`
* `EMAIL_PASSWORD=your_app_password`

### 3) DB 연결 테스트 및 실행
* DB 연결 확인: `python database.py`
* Flask 웹 애플리케이션 실행: `python app.py`

브라우저에서 `http://localhost:5000`으로 접속하여 대시보드를 확인합니다.

---
<br>

## 👥 9. 팀원 구성 및 역할 분담

| 팀원 | 담당 역할 | 주요 구현 내용 | 담당 파일 |
| :--- | :--- | :--- | :--- |
| 강민구 | Flask 웹 백엔드 | • Flask 라우팅 세팅 및 Jinja2 템플릿 데이터 바인딩<br>• `subscribers` 컬렉션 연동 (구독자 이메일, 선택 지역구 저장)<br>• 웹 화면 [지금 즉시 테스트 발송] 트리거 API 엔드포인트 구현 | `app.py` |
| 김서희 | 통계 & 하이브리드 추천 | • 최근 15회차 출현 빈도 분석 (Cold / Hot / Normal 그룹 분류)<br>• Cold 3 + Hot 2 + Normal 1 가중치 기반 샘플링 구현<br>• 번호 총합(100~175) 유효성 필터링 및 통계 분석 지표 산출 | `recommender.py` |
| 박준영 | 명당 데이터 정제 & 적재 | • 공공데이터포털 1등 당첨점 CSV 로드 (상호, 지역, 당첨 건수)<br>• '인터넷 복권판매사이트' 등 비매장 행 제외 전처리<br>• 카카오맵 검색 링크 필드 생성 후 MongoDB `lotto_stores` 적재 | `cleaner.py` |
| 유제우 | 당첨 번호 데이터 적재 | • 동행복권 역대 당첨 CSV 로드 및 Pandas 전처리<br>• 회차, 1~6번, 보너스 번호 정규화<br>• MongoDB `lotto_history` 컬렉션 일괄 적재 및 공통 DB 모듈 구축 | `database.py`<br>`data_loader.py` |
| 이재혁 | 지역구 필터링 & 랭킹 엔진 | • 사용자 선택 지역구 기준 매장 쿼리<br>• 당첨 건수 기준 내림차순 정렬 및 Top 3 매장 추출 함수 작성<br>• UI 드롭다운용 전체 시/군/구 유니크 목록 추출 함수 구현 | `store_filter.py` |
| 하지혜 | UI 대시보드 & HTML 메일러 | • 단일 페이지 반응형 웹 마크업 (지역 선택 드롭다운 & 명당 카드 UI)<br>• 로또 공 전용 CSS 스타일링 및 반응형 이메일 템플릿 디자인<br>• Gmail SMTP 연동 단체/개별 발송 모듈 구현 | `templates/index.html`<br>`notifier.py` |


---
<br>

### 📌 프로젝트 한계 및 분석적 시사점

* **독립시행 확률의 본질적 한계**
  * 로또 추첨은 매 회차 완벽한 독립시행이므로, 과거의 빈도 통계나 머신러닝/딥러닝 모델을 적용하더라도 **수학적인 당첨 확률(약 1/8,145,060)을 기술적으로 높이는 것은 불가능** 합니다.
* **서비스적 접근 의의**
  * 본 프로젝트의 목적은 '비과학적인 당첨 예측'이 아닌, **'공공데이터 및 통계 지표를 활용하여 무의미한 극단 조합(예: 1, 2, 3, 4, 5, 6 또는 극단적 합계)을 필터링하고, 사용자에게 데이터 기반의 합리적인 추천 경험을 제공하는 것'**에 초점을 두었습니다.


 
