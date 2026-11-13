import pandas as pd

def add_youth_single_household_lq(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for year in [2021, 2023, 2025]:
        
        youth_col = f"청년1인가구_{year}"
        total_col = f"전체1인가구_{year}"

        #전체 인구와 자치구별 인구 추출        
        seoul_ratio = result[youth_col].sum() / result[total_col].sum()
        district_ratio = result[youth_col] / result[total_col]


        result[f"청년1인가구_LQ_{year}"] =district_ratio/seoul_ratio
        col = f"청년1인가구_LQ_{year}"

        min_val = result[col].min()
        max_val = result[col].max()


        if max_val == min_val: #값이 같을 경우 0으로 나누는 것 방지
            result[f"청년1인가구_LQ_{year}_norm"] = 0.0
        else:
            result[f"청년1인가구_LQ_{year}_norm"] = (
            (result[f"청년1인가구_LQ_{year}"]-min_val) / (max_val - min_val)
            )
        
    return result

if __name__ == "__main__":
    df = pd.read_csv(
        "data/processed/youth_single_household_clean_2021_2025.csv",
        encoding="utf-8-sig"
    )

    result = add_youth_single_household_lq(df)

    print(result.head())

#결측치 검사 (이상 없음)
print(result.shape)
print(result.isna().sum())