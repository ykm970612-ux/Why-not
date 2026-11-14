import pandas as pd

def add_youth_population_lq(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()

    for year in [2021, 2023, 2025]: # 청년 인구 LQ 계산
        
        youth_col = f"청년인구_{year}"
        total_col = f"총인구_{year}"
        
        #서울시 전체 청년 인구 비율
        seoul_ratio = result[youth_col].sum() / result[total_col].sum()
        
        #자치구별 청년 인구 비율
        district_ratio = result[youth_col] / result[total_col]

        #result에 LQ값 저장
        result[f"청년인구_LQ_{year}"] = district_ratio/seoul_ratio
        col = f"청년인구_LQ_{year}"
        
        # Min-Max 정규화
        min_val = result[col].min()
        max_val = result[col].max()

        if min_val == max_val: #분모가 0이 되는 상황 방지
            result[f"청년인구_LQ_{year}_정규화"] = 0.0
        else:
            result[f"청년인구_LQ_{year}_정규화"] = (
                (result[f"청년인구_LQ_{year}"]-min_val)/(max_val-min_val) 
            ).round(4)



    return result

if __name__ == "__main__":
    df = pd.read_csv(
        "data/processed/youth_population_clean_2021_2025.csv",
        encoding="utf-8-sig"
    )

    result = add_youth_population_lq(df)

    print(result.filter(like="LQ").head())

    print(result.shape)
    print(result.isna().sum())
    
    for year in [2021, 2023, 2025]:
        col = f"청년인구_LQ_{year}_norm"
        print(year, result[col].min(), result[col].max())
