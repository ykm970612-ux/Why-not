import pandas as pd


def reverse_minmax(series):
    minimum = series.min()
    maximum = series.max()

    if minimum == maximum:
        return pd.Series(0.0, index=series.index)

    normalized = (maximum - series) / (maximum - minimum)

    return normalized.round(4)


def add_living_price_indicator(df):
    column = "생활물가지수"

    result = df.copy()

    values = pd.to_numeric(
        result[column],
        errors="raise",
    )

    result[column] = values
    result["생활물가지수_정규화"] = reverse_minmax(values)

    return result
