import os
import json
import pandas as pd
from data.mock_data import MOCK_STORES, MOCK_TOP_STORES

# 팀원 2가 정제한 JSON 파일 경로
JSON_FILE_NAME = "lotto_stores.json"


def load_store_data(file_path: str = JSON_FILE_NAME) -> pd.DataFrame:
    """
    팀원 2가 생성한 JSON 파일(lotto_stores.json)을 읽어 DataFrame으로 반환하는 함수.
    파일이 없을 경우 mock_data.py의 MOCK_STORES를 사용합니다.
    """
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            print(f"JSON 파일 로드 중 오류 발생: {e}")

    # JSON 파일이 없거나 로드 실패 시 가짜 데이터(MOCK_STORES) 사용
    return pd.DataFrame(MOCK_STORES)


def get_unique_regions(data=None) -> list:
    """
    드롭다운 메뉴용 전체 시/군/구 유니크 목록을 추출하는 함수
    :param data: DataFrame, dict 리스트 또는 None (None일 경우 load_store_data() 자동 실행)
    :return: 가나다순 정렬된 시/군/구 유니크 리스트
    """
    if data is None:
        df = load_store_data()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    # 필드명 대응 ('region' 또는 '지역')
    col_name = 'region' if 'region' in df.columns else ('지역' if '지역' in df.columns else None)
    
    if not col_name or col_name not in df.columns:
        return []

    # 결측치 제거 후 유니크 목록 가나다순 정렬
    unique_regions = df[col_name].dropna().unique().tolist()
    unique_regions.sort()
    return unique_regions


def get_top_stores_by_region(region: str, data=None, top_n: int = 3) -> list:
    """
    선택된 지역구 기준 매장 쿼리, 당첨 건수 내림차순 정렬 및 Top N 매장 추출 함수
    MOCK_TOP_STORES 규격(rank, store_name, region, win_count, search_url) 형태로 반환
    :param region: 검색할 지역구 텍스트 (예: "서울 서초구", "부산 동구")
    :param data: DataFrame, dict 리스트 또는 None (None일 경우 load_store_data() 자동 실행)
    :param top_n: 상위 추출 개수 (기본값 3)
    :return: Top N 매장 정보가 담긴 딕셔너리 리스트
    """
    if data is None:
        df = load_store_data()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    if 'region' not in df.columns:
        return []

    # 1. 지역구 필터링 (텍스트 포함 여부 검색)
    filtered_df = df[df['region'].astype(str).str.contains(region, na=False)].copy()

    if filtered_df.empty:
        return []

    # 2. 당첨 건수(win_count) 내림차순 정렬
    sort_col = 'win_count' if 'win_count' in filtered_df.columns else filtered_df.columns[0]
    sorted_df = filtered_df.sort_values(by=sort_col, ascending=False)

    # 3. Top N (상위 3개) 추출
    top_stores_df = sorted_df.head(top_n).copy()

    # 4. MOCK_TOP_STORES 규격에 맞게 순위(rank) 할당
    top_stores_df['rank'] = range(1, len(top_stores_df) + 1)

    # search_url 누락 시 자동 생성
    if 'search_url' not in top_stores_df.columns:
        top_stores_df['search_url'] = top_stores_df.apply(
            lambda row: f"https://map.kakao.com/link/search/{row.get('region', '')} {row.get('store_name', '')}", axis=1
        )

    # 출력 필드 정렬
    output_cols = ['rank', 'store_name', 'region', 'win_count', 'search_url']
    available_cols = [c for c in output_cols if c in top_stores_df.columns]

    return top_stores_df[available_cols].to_dict(orient='records')


# --- 사용 테스트 ---
if __name__ == "__main__":
    # 사용자가 전달해 준 JSON 데이터를 바로 객체로 테스트
    sample_data = [
        {"store_name": "오천억복권방", "region": "광주 서구", "win_count": 4, "search_url": "https://map.kakao.com/link/search/%EA%B4%91%EC%A3%BC%20%EC%84%9C%EA%B5%AC%20%EC%98%A4%EC%B2%9C%EC%96%B5%EB%B3%B5%EA%B6%8C%EB%B0%A9"},
        {"store_name": "로또킹", "region": "서울 영등포구", "win_count": 3, "search_url": "https://map.kakao.com/link/search/%EC%84%9C%EC%9A%B8%20%EC%98%81%EB%93%B1%ED%8F%AC%EA%B5%AC%20%EB%A1%9C%EB%98%90%ED%82%B9"},
        {"store_name": "오케이상사", "region": "서울 서초구", "win_count": 3, "search_url": "https://map.kakao.com/link/search/%EC%84%9C%EC%9A%B8%20%EC%84%9C%EC%B4%88%EA%B5%AC%20%EC%98%A4%EC%BC%80%EC%9D%B4%EC%83%81%EC%82%AC"},
        {"store_name": "주황이 복권방", "region": "서울 서초구", "win_count": 1, "search_url": "https://map.kakao.com/link/search/%EC%84%9C%EC%9A%B8%20%EC%84%9C%EC%B4%88%EA%B5%AC%20%EC%A3%BC%ED%99%A9%EC%9D%B4%20%EB%B3%B5%EA%B6%8C%EB%B0%A9"},
        {"store_name": "부일카서비스", "region": "부산 동구", "win_count": 3, "search_url": "https://map.kakao.com/link/search/%EB%B6%80%EC%82%B0%20%EB%8F%99%EA%B5%AC%20%EB%B6%80%EC%9D%BC%EC%B9%B4%EC%84%9C%EB%B9%84%EC%8A%A4"},
        {"store_name": "천하명당초량점", "region": "부산 동구", "win_count": 1, "search_url": "https://map.kakao.com/link/search/%EB%B6%80%EC%82%B0%20%EB%8F%99%EA%B5%AC%20%EC%B2%9C%ED%95%98%EB%AA%85%EB%8B%B9%EC%B4%88%EB%9F%89%EC%A0%90"},
        {"store_name": "돈벼락맞는곳", "region": "부산 동구", "win_count": 1, "search_url": "https://map.kakao.com/link/search/%EB%B6%80%EC%82%B0%20%EB%8F%99%EA%B5%AC%20%EB%8F%88%EB%B2%BC%EB%9D%BD%EB%A7%9E%EB%8A%94%EA%B3%B3"}
    ]

    print("1. 유니크 지역 목록 테스트:")
    regions = get_unique_regions(sample_data)
    print("지역 목록:", regions)

    print("\n2. '부산 동구' Top 3 매장 조회 테스트:")
    top3_busan = get_top_stores_by_region("부산 동구", sample_data)
    for store in top3_busan:
        print(f"{store['rank']}위: {store['store_name']} ({store['win_count']}회 당첨)")

    print("\n3. '서울 서초구' Top 3 매장 조회 테스트:")
    top3_seocho = get_top_stores_by_region("서울 서초구", sample_data)
    for store in top3_seocho:
        print(f"{store['rank']}위: {store['store_name']} ({store['win_count']}회 당첨)")