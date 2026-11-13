import pandas as pd


def reverse_minmax(series):
    minimum = series.min()
    maximum = series.max()

    if minimum == maximum:
        return pd.Series(0.0, index=series.index)

    return ((maximum - series) / (maximum - minimum)).round(4)


def add_rent_indicators(df):
    columns = [
        "환산월세_2025_만원",
        "변화율_2021_2025_퍼센트",
    ]

    result = df.copy()

    for column in columns:
        values = pd.to_numeric(result[column], errors="raise")

        result[column] = values

    result["환산월세_2025_정규화"] = reverse_minmax(result["환산월세_2025_만원"])

    result["월세변화율_정규화"] = reverse_minmax(result["변화율_2021_2025_퍼센트"])

    return result
