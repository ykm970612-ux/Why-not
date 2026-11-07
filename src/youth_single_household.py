import pandas as pd

df25 = pd.read_csv(
    "data/raw/youth_single_household_2025_kosis.csv",
    encoding="cp949",
    skiprows=2
)

df23 = pd.read_csv(
    "data/raw/youth_single_household_2023_kosis.csv",     
    encoding="cp949",
    skiprows = 2
)

df21 = pd.read_csv(
    "data/raw/youth_single_household_2021_kosis.csv",
    encoding="cp949",
    skiprows=2
)

combined_df = pd.concat([df21, df23, df25], ignore_index=True)

#print(combined_df.shape)
#print(combined_df["시점"].unique())

ages = ["20~24세", "25~29세", "30~34세", "35~39세"]

youth_df =  combined_df[combined_df["연령별"].isin(ages)]

condition1 = youth_df["C행정구역별(시군구)"].str.len() == 6
condition2 = youth_df["C행정구역별(시군구)"].str.startswith("'11")

seoul_df = youth_df[condition2 & condition1]
seoul_df["1인가구"] = pd.to_numeric(seoul_df["1인가구"])

result = seoul_df.groupby(["행정구역별(시군구)", "시점"])["1인가구"].sum()

#인데스를 일반 컬럼으로 변환
result = result.reset_index()

#공백 제거
result["행정구역별(시군구)"] = result["행정구역별(시군구)"].str.strip()

#명칭 통일
result = result.rename(
    columns={"행정구역별(시군구)": "자치구명"}
)
#결측치 검사 (이상 없음)
#print(result.isnull().sum())
#중복검사 (이상 없음)
#print(result.duplicated(subset=["자치구명", "시점"]).sum())


#열, 행 변환하여 시점을 열로 옮김
wide_df = result.pivot(
    index="자치구명",
    columns="시점",
    values="1인가구"
)

#인덱스를 일반 칼럼으로 변환
wide_df = wide_df.reset_index()


#열 이름 변경
wide_df = wide_df.rename(
    columns={
        2021: "청년1인가구_2021",
        2023: "청년1인가구_2023",
        2025: "청년1인가구_2025"
    }
)

#시점별 1인가구 총합
total_2025 = wide_df["청년1인가구_2025"].sum()
total_2021 = wide_df["청년1인가구_2021"].sum()
total_2023 = wide_df["청년1인가구_2023"].sum()

#raw에 있는 서울 특별시 전체 합
seoul_total = combined_df[
    combined_df["C행정구역별(시군구)"] == "'11"
]

#자료에 있는 서울시 총합과 재구성한 합이 일치하는지 검사하기 위해 만듦
seoul_total_youth = seoul_total[seoul_total["연령별"].isin(ages)].copy()

seoul_total_youth["1인가구"] = pd.to_numeric(seoul_total_youth["1인가구"])
seoul_total_result = seoul_total_youth.groupby("시점")["1인가구"].sum()

#저장
wide_df.to_csv(
    "data/processed/youth_single_household_clean_2025.csv",
    index=False,
    encoding="utf-8-sig"
)


check_df = pd.read_csv(
    "data/processed/youth_single_household_clean_2025.csv",
    encoding="utf-8-sig"
)

print(check_df.shape)
print(check_df.columns)
print(check_df.head())