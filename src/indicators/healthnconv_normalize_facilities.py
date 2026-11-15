from pathlib import Path

import geopandas as gpd
import pandas as pd


BOUNDARY_FILE = Path(__file__).resolve().parents[2] / "data/raw/seoul.geojson.json"


def _district_areas_km2() -> pd.Series:
    if not BOUNDARY_FILE.is_file():
        raise FileNotFoundError(f"DataForge 서울 자치구 경계 파일이 필요합니다: {BOUNDARY_FILE}")

    boundaries = gpd.read_file(BOUNDARY_FILE)
    if "name" not in boundaries or boundaries["name"].isna().any():
        raise ValueError("경계 파일에 자치구명(name)이 필요합니다.")
    names = boundaries["name"].str.strip()
    if names.eq("").any() or names.duplicated().any():
        raise ValueError("경계 파일의 자치구명이 비어 있거나 중복되었습니다.")

    # GeoJSON의 경위도를 미터 단위 등적 좌표계로 변환한다.
    if boundaries.crs is None:
        boundaries = boundaries.set_crs("EPSG:4326")
    areas = boundaries.to_crs("EPSG:6933").area / 1_000_000
    if areas.isna().any() or areas.isin([float("inf"), float("-inf")]).any() or areas.le(0).any():
        raise ValueError("경계 파일에 유효하지 않은 자치구 면적이 있습니다.")
    return pd.Series(areas.to_numpy(), index=names)


def _minmax(values: pd.Series) -> pd.Series:
    low, high = values.min(), values.max()
    if low == high:
        return pd.Series(0.0, index=values.index)
    return ((values - low) / (high - low)).round(4)


def add_healthnconv_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """시설 수와 1㎢당 시설 수의 Min-Max 지표를 추가한 복사본을 반환한다."""
    columns = ("일상의료시설수", "종합의료시설수", "생활편의시설수")
    missing = [column for column in ("자치구명", *columns) if column not in df.columns]
    if missing:
        raise ValueError(f"정규화에 필요한 통합 데이터 열이 없습니다: {missing}")

    result = df.copy()
    names = df["자치구명"].astype("string").str.strip()
    areas = names.map(_district_areas_km2())
    if areas.isna().any():
        raise ValueError(f"면적을 찾지 못한 자치구: {names[areas.isna()].tolist()}")
    result["자치구면적_km2"] = areas

    for column in columns:
        values = pd.to_numeric(df[column])
        if values.empty or values.isna().any() or values.isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"{column}에 정규화할 수 없는 값이 있습니다.")
        result[f"{column}_정규화"] = _minmax(values)

        density = values / areas
        density_column = f"{column}_km2당"
        result[density_column] = density
        result[f"{density_column}_정규화"] = _minmax(density)
    return result
