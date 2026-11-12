from pathlib import Path
import pandas as pd
import geopandas as gpd

# 1. 파일 경로
PROJECT_DIR = Path(__file__).resolve().parents[2]
BUS_FILE = PROJECT_DIR / "data" / "raw" / 'bus_stops_2025_seoul.xlsx'
BOUNDARY_FILE = PROJECT_DIR / "data" / "raw" / 'seoul.geojson.json'
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / '서울시_버스_전처리결과'


def minmax(series):
    # 최댓값과 최솟값이 같으면 0으로 처리
    minimum, maximum = series.min(), series.max()
    if maximum == minimum:
        return pd.Series(0.0, index=series.index)

    normalized = (series - minimum) / (maximum - minimum)
    return normalized.round(4)


def main():
    # 2. 원본 데이터 읽기 및 검증
    bus = pd.read_excel(
        BUS_FILE,
        sheet_name='Data',
        dtype={'NODE_ID': 'string', 'ARS_ID': 'string'},
    )
    districts = gpd.read_file(BOUNDARY_FILE).to_crs('EPSG:4326')
    required = {'NODE_ID', 'ARS_ID', '정류소명', 'X좌표', 'Y좌표', '정류소타입'}
    if not required.issubset(bus.columns):
        raise ValueError(f'버스 파일 누락 컬럼: {sorted(required - set(bus.columns))}')
    if not {'code', 'name'}.issubset(districts.columns) or len(districts) != 25:
        raise ValueError('자치구 경계 파일의 code/name 또는 25개 자치구를 확인하세요.')
    districts = districts[['code', 'name', 'geometry']].rename(
        columns={'code': '자치구코드', 'name': '자치구명'}
    )
    districts['자치구코드'] = districts['자치구코드'].astype(str)

    # 3. 좌표를 숫자로 변환하고 유효한 정류소만 공간 분류
    bus = bus.copy().reset_index(drop=True)
    bus.insert(0, '원본행번호', range(1, len(bus) + 1))
    for col in ['X좌표', 'Y좌표']:
        bus[col] = pd.to_numeric(bus[col], errors='coerce')
    valid_mask = (
        bus['X좌표'].between(124, 132)
        & bus['Y좌표'].between(33, 39)
    )
    invalid = bus.loc[~valid_mask].copy()
    valid = bus.loc[valid_mask].copy()
    points = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid['X좌표'], valid['Y좌표']),
        crs='EPSG:4326',
    )
    joined = gpd.sjoin(points, districts, how='left', predicate='within')

    # 4. 경계선 위의 정류소는 intersects로 한 번 더 확인
    missing_ids = joined.loc[joined['자치구명'].isna(), '원본행번호']
    if not missing_ids.empty:
        boundary_points = points[points['원본행번호'].isin(missing_ids)]
        boundary_hits = gpd.sjoin(
            boundary_points, districts, how='left', predicate='intersects'
        )
        boundary_hits = (
            boundary_hits
            .sort_values(['원본행번호', '자치구코드'])
            .drop_duplicates('원본행번호')
        )
        lookup = boundary_hits.set_index('원본행번호')
        for col in ['자치구코드', '자치구명']:
            mask = joined['자치구명'].isna()
            joined.loc[mask, col] = joined.loc[mask, '원본행번호'].map(lookup[col])
    joined = (
        joined
        .sort_values(['원본행번호', '자치구코드'])
        .drop_duplicates('원본행번호')
    )
    matched = joined[joined['자치구명'].notna()].drop(columns=['geometry', 'index_right'])
    unmatched = joined[joined['자치구명'].isna()].drop(columns=['geometry', 'index_right'])

    # 5. 서울 25개 자치구별 정류소 수 집계 및 Min-Max 정규화
    counts = matched.groupby('자치구코드').size().rename('정류소수')
    summary = districts[['자치구코드', '자치구명']].merge(
        counts, on='자치구코드', how='left'
    )
    summary['정류소수'] = summary['정류소수'].fillna(0).astype(int)
    summary['정류소수_minmax'] = minmax(summary['정류소수'])
    summary = summary.sort_values('자치구코드').reset_index(drop=True)

    # 6. 결과 저장
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(
        OUTPUT_DIR / '자치구별_버스정류소_집계.csv',
        index=False,
        encoding='utf-8-sig',
    )
    with pd.ExcelWriter(OUTPUT_DIR / '버스정류소_자치구별_전처리결과.xlsx') as writer:
        summary.to_excel(writer, sheet_name='자치구별_집계_정규화', index=False)
        matched.to_excel(writer, sheet_name='정류소별_분류', index=False)
        unmatched.to_excel(writer, sheet_name='자치구_미분류', index=False)
        invalid.to_excel(writer, sheet_name='좌표오류', index=False)
    print(
        f'완료: 원본 {len(bus)}개 / 분류 {len(matched)}개 / '
        f'미분류 {len(unmatched)}개 / 좌표오류 {len(invalid)}개'
    )
    print(f'저장 위치: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
