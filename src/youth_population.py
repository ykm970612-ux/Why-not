import pandas as pd

#파일 읽기
df25 = pd.read_csv(
    "data/raw/youth_population_2025.csv",
    encoding="cp949"
)

df23 = pd.read_csv(
    "data/raw/youth_population_2023.csv",
    encoding="cp949"
)

df21 = pd.read_csv(
    "data/raw/youth_population_2021.csv",
    encoding="cp949"
)

#행정구역, 20~39세 거주자, 해당 년도 총 인구수만 선택
df25_selected = df25[
    [
        "행정구역",
        "2025년_거주자_20~29세",
        "2025년_거주자_30~39세",
        "2025년_거주자_총인구수"
    ]
].copy()

df23_selected = df23[
    [
        "행정구역",
        "2023년_거주자_20~29세",
        "2023년_거주자_30~39세",
        "2023년_거주자_총인구수"
    ]
].copy()

df21_selected = df21[
    [
        "행정구역",
        "2021년_거주자_20~29세",
        "2021년_거주자_30~39세",
        "2021년_거주자_총인구수"
    ]
].copy()

#서울특별시에 해당하는 행정구역만 선택
condition1_25 = df25_selected["행정구역"].str.startswith("서울특별시")
condition2_25 = df25_selected["행정구역"].str.contains("구 (", regex=False)

condition1_23 = df23_selected["행정구역"].str.startswith("서울특별시")
condition2_23 = df23_selected["행정구역"].str.contains("구 (", regex=False)

condition1_21 = df21_selected["행정구역"].str.startswith("서울특별시")
condition2_21 = df21_selected["행정구역"].str.contains("구 (", regex=False)

seoul25 = df25_selected[
    (condition1_25) & (condition2_25)
].copy()

seoul23 = df23_selected[
    (condition1_23) & (condition2_23)
].copy()

seoul21 = df21_selected[
    (condition1_21) & (condition2_21)
]

#거주자 연령별 명칭 통합
seoul25 = seoul25.rename(
    columns= {"2025년_거주자_20~29세": "20~29세",
              "2025년_거주자_30~39세" : "30~39세"
              }
)

seoul23 = seoul23.rename(
    columns= {"2023년_거주자_20~29세": "20~29세",
              "2023년_거주자_30~39세" : "30~39세"
              }
)

seoul21 = seoul21.rename(
    columns= {"2021년_거주자_20~29세": "20~29세",
              "2021년_거주자_30~39세" : "30~39세"
              }
)

#문자형을 숫자형으로 변환
seoul25["20~29세"] = pd.to_numeric(
    seoul25["20~29세"].str.replace(",","")
)
seoul25["30~39세"] = pd.to_numeric(
    seoul25["30~39세"].str.replace(",","")
)

seoul23["20~29세"] = pd.to_numeric(
    seoul23["20~29세"].str.replace(",","")
)
seoul23["30~39세"] = pd.to_numeric(
    seoul23["30~39세"].str.replace(",","")
)

seoul21["20~29세"] = pd.to_numeric(
    seoul21["20~29세"].str.replace(",","")
)
seoul21["30~39세"] = pd.to_numeric(
    seoul21["30~39세"].str.replace(",","")
)


#청년인구 열로 20~39세 인구 통합
seoul25["청년인구"] = seoul25["20~29세"] + seoul25["30~39세"]
seoul23["청년인구"] = seoul23["20~29세"] + seoul23["30~39세"]
seoul21["청년인구"] = seoul21["20~29세"] + seoul21["30~39세"]

#행정구역 ---> 자치구명으로 변경 
seoul25["자치구명"] = seoul25["행정구역"].str.split().str[1].copy()
seoul23["자치구명"] = seoul23["행정구역"].str.split().str[1].copy()
seoul21["자치구명"] = seoul21["행정구역"].str.split().str[1].copy()

#자치구 전체 인구수 ->> 총인구수
seoul25["총인구수"] = pd.to_numeric(
    seoul25["2025년_거주자_총인구수"].str.replace(",","")
)
seoul23["총인구수"] = pd.to_numeric(
    seoul23["2023년_거주자_총인구수"].str.replace(",","")
)
seoul21["총인구수"] = pd.to_numeric(
    seoul21["2021년_거주자_총인구수"].str.replace(",","")
)

#pop연도로 데이터 프레임 새로 구성
pop25 = seoul25[
                ["자치구명", 
                 "청년인구", 
                 "총인구수"]
                ].copy()

pop23 = seoul23[
                ["자치구명", 
                 "청년인구",
                 "총인구수"]
                ].copy()

pop21 = seoul21[
                ["자치구명", 
                 "청년인구", 
                 "총인구수"]
                ].copy()

#명칭 변경
pop25 = pop25.rename(
    columns={
        "청년인구": "청년인구_2025",
        "총인구수": "총인구_2025"
    }
)

pop23 = pop23.rename(
    columns={
        "청년인구": "청년인구_2023",
        "총인구수": "총인구_2023"
    }
)

pop21 = pop21.rename(
    columns={
        "청년인구": "청년인구_2021",
        "총인구수": "총인구_2021"
    }
)


#자치구명을 기준으로 병합
merged_df = pd.merge(
    pop21,
    pop23,
    on="자치구명"
)

final_df = pd.merge(
    merged_df,
    pop25,
    on="자치구명"
)

print(final_df.shape)

#결측치, 중복, 자료형 확인 

# print(final_df.isnull().sum())
# print(final_df["자치구명"].duplicated().sum())
# print(final_df.dtypes)

#청년인구의 합이 총인구수를 넘는지 확인

# print(
#     (final_df["청년인구_2025"] > final_df["총인구_2025"]).sum()
# )
# print(
#     (final_df["청년인구_2021"] > final_df["총인구_2021"]).sum()
# )
# print(
#     (final_df["청년인구_2023"] > final_df["총인구_2023"]).sum()
# )

#파일로 저장
final_df.to_csv(
    "data/processed/youth_population_2021_2025.csv",
    index=False,
    encoding="utf-8-sig"
)

check_df = pd.read_csv(
    "data/processed/youth_population_2021_2025.csv",
    encoding="utf-8-sig"
)

print(final_df.compare(check_df))