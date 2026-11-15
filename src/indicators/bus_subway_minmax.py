import pandas as pd


def add_minmax_columns(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for column in ("버스정류소수", "물리적_역수"):
        if column not in result.columns:
            continue

        values = pd.to_numeric(result[column], errors="raise")
        minimum = values.min()
        maximum = values.max()
        output_column = f"{column}_정규화"

        if pd.isna(minimum) or maximum == minimum:
            result[output_column] = 0.0
        else:
            result[output_column] = (
                (values - minimum) / (maximum - minimum)
            ).round(4)

    return result
