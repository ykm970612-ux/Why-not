import pandas as pd
import geopandas as gpd

#geojson_path / 경로 : data/raw/seoul.geojson.json
def apply_density(df: pd.DataFrame, geojson_path) -> pd.DataFrame:
    result = df.copy()

    # 자치구별 면적 계산 (m² → km²)
    boundary = gpd.read_file(geojson_path).to_crs(epsg=5179)
    boundary['면적_km2'] = boundary.geometry.area / 1_000_000
    area = boundary.groupby('name')['면적_km2'].sum()

    # 각 자치구에 해당하는 면적 연결
    district_area = result['자치구명'].map(area)
    if district_area.isna().any() or (district_area <= 0).any():
        raise ValueError('자치구 면적 데이터 오류')

    # 기존 시설수 컬럼의 값만 변경
    for column in ('버스정류소수', '물리적_역수'):
        if column not in result.columns:
            continue

        values = pd.to_numeric(result[column], errors='raise')
        if values.isna().any() or (values < 0).any():
            raise ValueError(f'{column} 데이터 오류')
        result[column] = values / district_area

    return result
