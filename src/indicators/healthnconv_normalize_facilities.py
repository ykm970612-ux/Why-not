import pandas as pd


def add_healthnconv_indicators(df: pd.DataFrame) -> pd.DataFrame:
    columns = ("일상의료시설수", "종합의료시설수", "생활편의시설수")
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise ValueError(f"정규화에 필요한 통합 데이터 열이 없습니다: {missing}")

    result = df.copy()
    for column in columns:
        values = pd.to_numeric(df[column])
        if values.empty or values.isna().any() or values.isin([float("inf"), float("-inf")]).any():
            raise ValueError(f"{column}에 정규화할 수 없는 값이 있습니다.")
        low, high = values.min(), values.max()
        if low == high:
            result[f"{column}_정규화"] = 0.0
        else:
            scaled = (values - low) / (high - low)
            result[f"{column}_정규화"] = scaled.round(4)
    return result
