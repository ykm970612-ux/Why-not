from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "youth_single_household_clean_2021_2025.csv"

df25 = pd.read_csv(
    RAW_DIR / "youth_single_household_2025_kosis.csv",
    encoding="cp949",
    skiprows=2,
)

df23 = pd.read_csv(
    RAW_DIR / "youth_single_household_2023_kosis.csv",
    encoding="cp949",
    skiprows=2,
)

df21 = pd.read_csv(
    RAW_DIR / "youth_single_household_2021_kosis.csv",
    encoding="cp949",
    skiprows=2,
)

combined_df = pd.concat([df21, df23, df25], ignore_index=True)

# print(combined_df.shape)
# print(combined_df["시점"].unique())

ages = ["20~24세", "25~29세", "30~34세", "35~39세"]

youth_df = combined_df[combined_df["연령별"].isin(ages)]
total_df = combined_df[combined_df["연령별"] == "합계"]


condition1 = youth_df["C행정구역별(시군구)"].str.len() == 6
condition2 = youth_df["C행정구역별(시군구)"].str.startswith("'11")

total_conditon1 = total_df["C행정구역별(시군구)"].str.len() == 6
total_conditon2 = total_df["C행정구역별(시군구)"].str.startswith("'11")

seoul_df = youth_df[condition2 & condition1].copy()
seoul_df["1인가구"] = pd.to_numeric(seoul_df["1인가구"])

seoul_total_df = total_df[total_conditon1 & total_conditon2].copy()

result = seoul_df.groupby(["행정구역별(시군구)", "시점"])["1인가구"].sum()

# 문자열을 숫자형으로 변환
seoul_total_df["1인가구"] = pd.to_numeric(seoul_total_df["1인가구"])

# 자치구와 연도별로 집계
total_result = seoul_total_df.groupby(
    ["행정구역별(시군구)", "시점"]
)["1인가구"].sum().reset_index()


#자치구명 통일
total_result["행정구역별(시군구)"] = (
    total_result["행정구역별(시군구)"].str.strip()
)

total_result = total_result.rename(
    columns={"행정구역별(시군구)": "자치구명"}
)
# 인데스를 일반 컬럼으로 변환
result = result.reset_index()

# 공백 제거
result["행정구역별(시군구)"] = result["행정구역별(시군구)"].str.strip()

# 명칭 통일
result = result.rename(columns={"행정구역별(시군구)": "자치구명"})
# 결측치 검사 (이상 없음)
# print(result.isnull().sum())
# 중복검사 (이상 없음)
# print(result.duplicated(subset=["자치구명", "시점"]).sum())


# 열, 행 변환하여 시점을 열로 옮김
wide_df = result.pivot(index="자치구명", columns="시점", values="1인가구")

# 인덱스를 일반 칼럼으로 변환
wide_df = wide_df.reset_index()


# 열 이름 변경
wide_df = wide_df.rename(
    columns={
        2021: "청년1인가구_2021",
        2023: "청년1인가구_2023",
        2025: "청년1인가구_2025",
    }
)

total_wide_df = total_result.pivot(
    index="자치구명",
    columns="시점",
    values="1인가구"
)

total_wide_df = total_wide_df.reset_index()

total_wide_df = total_wide_df.rename(
    columns={
        2021: "전체1인가구_2021",
        2023: "전체1인가구_2023",
        2025: "전체1인가구_2025"
    }
)

final_df = pd.merge(
    wide_df,
    total_wide_df,
    on="자치구명",
    how="inner",
    validate="one_to_one"
)

# 시점별 1인가구 총합
total_2025 = wide_df["청년1인가구_2025"].sum()
total_2021 = wide_df["청년1인가구_2021"].sum()
total_2023 = wide_df["청년1인가구_2023"].sum()

# raw에 있는 서울 특별시 전체 합
seoul_total = combined_df[combined_df["C행정구역별(시군구)"] == "'11"]

# 자료에 있는 서울시 총합과 재구성한 합이 일치하는지 검사하기 위해 만듦
seoul_total_youth = seoul_total[seoul_total["연령별"].isin(ages)].copy()

seoul_total_youth["1인가구"] = pd.to_numeric(seoul_total_youth["1인가구"])
seoul_total_result = seoul_total_youth.groupby("시점")["1인가구"].sum()

print("데이터 크기:", final_df.shape)
print("결측치:", final_df.isnull().sum().sum())
print("중복 자치구:", final_df["자치구명"].duplicated().sum())

for year in [2021, 2023, 2025]:
    invalid = (
        final_df[f"청년1인가구_{year}"]
        > final_df[f"전체1인가구_{year}"]
    ).sum()
    print(f"{year}년 이상치:", invalid)


# 저장
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
final_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")


check_df = pd.read_csv(OUTPUT_FILE, encoding="utf-8-sig")

print(final_df.shape)
print(final_df.head())