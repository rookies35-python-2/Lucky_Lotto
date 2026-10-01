import pandas as pd
from database import get_collection, LOTTO_STORES
from data.mock_data import MOCK_STORES


def load_store_data(query: dict = None) -> pd.DataFrame:
    """
    MongoDB의 lotto_stores 컬렉션에서 매장 데이터를 조회하여 DataFrame으로 반환합니다.
    연결 및 로드 실패 시 mock_data.py의 MOCK_STORES를 사용합니다.
    """
    try:
        stores_col = get_collection(LOTTO_STORES)
        filter_query = query if query else {}
        cursor = stores_col.find(filter_query, {"_id": 0})
        data = list(cursor)

        if data:
            return pd.DataFrame(data)
    except Exception as e:
        print(f"MongoDB 로드 실패, MOCK 데이터 사용: {e}")

    return pd.DataFrame(MOCK_STORES)


def get_unique_regions(data=None) -> list:
    """
    드롭다운 메뉴용 전체 시/군/구 유니크 목록을 추출하는 함수.
    """
    if data is None:
        try:
            stores_col = get_collection(LOTTO_STORES)
            unique_regions = stores_col.distinct("region")
            unique_regions.sort()
            return unique_regions
        except Exception:
            df = load_store_data()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
    else:
        df = data.copy()

    col_name = 'region' if 'region' in df.columns else ('지역' if '지역' in df.columns else None)
    if not col_name or col_name not in df.columns:
        return []

    unique_regions = df[col_name].dropna().unique().tolist()
    unique_regions.sort()
    return unique_regions


def get_top_stores_by_region(region: str, data=None, top_n: int = 3) -> list:
    """
    선택된 지역구 기준 매장 쿼리, 당첨 건수 내림차순 정렬 및 Top N 매장 추출 함수
    """
    if data is None:
        try:
            stores_col = get_collection(LOTTO_STORES)
            cursor = stores_col.find(
                {"region": {"$regex": region}}, 
                {"_id": 0}
            ).sort("win_count", -1).limit(top_n)
            
            top_stores = list(cursor)
            if top_stores:
                df = pd.DataFrame(top_stores)
            else:
                return []
        except Exception:
            df = load_store_data()
            df = df[df['region'].astype(str).str.contains(region, na=False)].copy()
    elif isinstance(data, list):
        df = pd.DataFrame(data)
        df = df[df['region'].astype(str).str.contains(region, na=False)].copy()
    else:
        df = data.copy()
        df = df[df['region'].astype(str).str.contains(region, na=False)].copy()

    if df.empty or 'region' not in df.columns:
        return []

    sort_col = 'win_count' if 'win_count' in df.columns else df.columns[0]
    top_stores_df = df.sort_values(by=sort_col, ascending=False).head(top_n).copy()

    top_stores_df['rank'] = range(1, len(top_stores_df) + 1)

    if 'search_url' not in top_stores_df.columns:
        top_stores_df['search_url'] = top_stores_df.apply(
            lambda row: f"https://map.kakao.com/link/search/{row.get('region', '')} {row.get('store_name', '')}", axis=1
        )

    output_cols = ['rank', 'store_name', 'region', 'win_count', 'search_url']
    available_cols = [c for c in top_stores_df.columns if c in output_cols]

    return top_stores_df[available_cols].to_dict(orient='records')


# --- 직접 실행 테스트 ---
if __name__ == "__main__":
    print("1. DB 연동 유니크 지역 목록:")
    print(get_unique_regions())

    print("\n2. '서울 서초구' Top 3 매장:")
    print(get_top_stores_by_region("서울 서초구"))