from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import os

#한글 글꼴 지정하여 깨지는 부분 수정
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False


#자치구 청년 LQ 정규화 시각화 코드
data_dir = Path("data/processed")

files = [
    "youth_single_household_clean_2021_2025.csv",
    "rent_trend_2021_2025.csv",
    "rent_2021_2025_district.csv",
    "seoul_youth_integrated_2025.csv"
]

# for filename in files:
#     df = pd.read_csv(data_dir / filename, encoding="utf-8-sig", nrows=2)
    
#     print(f"\n파일명: {filename}")
#     print(df.columns.tolist())
#     print(df.head(2))

years = [2021, 2023, 2025]

normalized_df = pd.read_csv(
    data_dir / "seoul_youth_normalized_2025.csv",
    encoding="utf-8-sig"
)
lq_cols = [col for col in normalized_df.columns if "LQ" in col]

#자치구명으로 정렬
normalized_df = normalized_df.sort_values("자치구명")

#작은 그래프 25칸(5*5) 생성
fig, axes = plt.subplots(5, 5, figsize=(20, 20))
#1차원으로 축소
axes = axes.flatten()

for i, (_, row) in enumerate(normalized_df.iterrows()):
    ax = axes[i]

    lq_values = [
        row["청년1인가구_LQ_2021"],
        row["청년1인가구_LQ_2023"],
        row["청년1인가구_LQ_2025"]
    ]

    ax.plot(years, lq_values, marker="o")
    ax.axhline(y=1, linestyle="--")
    ax.set_title(row["자치구명"], fontsize=10)
    ax.set_xticks(years)

fig.suptitle("서울 25개 자치구 청년 1인가구 LQ 변화 (2021, 2023, 2025)", fontsize=18)
fig.tight_layout(rect=[0, 0, 1, 0.97])

os.makedirs("outputs/charts", exist_ok=True)
plt.savefig("outputs/charts/youth_single_household_lq_trend.png", dpi=300, bbox_inches="tight")
plt.close()


#환산월세 시각화 코드
rent_df = pd.read_csv(
    data_dir / "rent_trend_2021_2025.csv",
    encoding="utf-8-sig"
)

#자치구 정렬
rent_df = rent_df.sort_values("자치구명")

#연도 정의
years = [2021, 2023, 2025]

#그래프에 필요한 열 선택
rent_cols = [
    "환산월세_2021_만원",
    "환산월세_2023_만원",
    "환산월세_2025_만원"
]

#그래프 공간 생성
fig, axes = plt.subplots(5, 5, figsize=(20, 20), sharey=True)

#1차원으로 펼치기
axes = axes.flatten()

for i, (_, row) in enumerate(rent_df.iterrows()):
    ax = axes[i]
    rent_values = row[rent_cols].tolist()
    ax.plot(years, rent_values, marker="o")
    ax.set_title(row["자치구명"], fontsize=10)
    ax.set_xticks(years)

    #모든 그래프에 y축이랑 단위 표시
    ax.tick_params(axis="y", labelleft=True)
#제목 및 단위 표시
fig.suptitle("서울 25개 자치구 환산월세 변화 (2021~2025)", fontsize=18)
fig.supylabel("환산월세 (만원)")

#그래프 간격 조정 
fig.tight_layout(rect=[0.03, 0, 1, 0.97])

#파일 저장
output_dir = Path("outputs/charts")
output_dir.mkdir(parents=True, exist_ok=True)

fig.savefig(output_dir / "rent_trend_2021_2025.png", dpi=300, bbox_inches="tight")
plt.close(fig)

print("자치구 청년LQ 시각화 및 환산월세 시각화 완료")

#청년 인구 LQ 변화량 계산
lq_analysis = normalized_df[
    ["자치구명", "청년1인가구_LQ_2021", "청년1인가구_LQ_2025"]
].copy()

lq_analysis["LQ_변화량"] = (
    lq_analysis["청년1인가구_LQ_2025"]
    - lq_analysis["청년1인가구_LQ_2021"]
)

#LQ가 가장 많이 증가한 지역 찾기
lq_analysis = lq_analysis.sort_values("LQ_변화량", ascending=False)

#상위 5개 지역
print("LQ 증가 상위 5개 자치구")
print(lq_analysis.head(5))

#하위 5개지역
print("\nLQ 변화량 하위 5개 자치구")
print(lq_analysis.tail(5))

#분석에 필요한 컬럼 선택
rent_analysis = rent_df[
    [
        "자치구명",
        "환산월세_2021_만원",
        "환산월세_2025_만원",
        "변화액_2021_2025_만원",
        "변화율_2021_2025_퍼센트"
    ]
].copy()

#환산월세 증가액 기준으로 정렬
rent_analysis = rent_analysis.sort_values(
    "변화액_2021_2025_만원",
    ascending=False
)

#증가액 상위 5개 자치구 확인
print("\n환산월세 증가액 상위 5개 자치구")
print(rent_analysis.head(5).to_string(index=False))

#증가액 하위 5개 자치구 확인
print("\n환산월세 증가액 하위 5개 자치구")
print(rent_analysis.tail(5).to_string(index=False))

#두 데이터 병합
comparison_df = pd.merge(
    lq_analysis,
    rent_analysis,
    on="자치구명",
    how="inner",
    validate="one_to_one"
)

#데이터 개수 확인
print("분석 대상 자치구 수:", len(comparison_df))

#필요 컬럼 출력
print(
    comparison_df[
        [
            "자치구명",
            "LQ_변화량",
            "변화율_2021_2025_퍼센트"
        ]
    ].to_string(index=False)
)

#상관계수 확인
correlation = comparison_df["LQ_변화량"].corr(
    comparison_df["변화율_2021_2025_퍼센트"]
)

#상관계수 출력
print(f"LQ 변화량과 환산월세 증가율의 상관계수: {correlation:.4f}")