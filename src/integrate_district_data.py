from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
OUTPUT_FILE = PROCESSED_DIR / "seoul_youth_integrated_2025.csv"

DISTRICTS = [
    "종로구",
    "중구",
    "용산구",
    "성동구",
    "광진구",
    "동대문구",
    "중랑구",
    "성북구",
    "강북구",
    "도봉구",
    "노원구",
    "은평구",
    "서대문구",
    "마포구",
    "양천구",
    "강서구",
    "구로구",
    "금천구",
    "영등포구",
    "동작구",
    "관악구",
    "서초구",
    "강남구",
    "송파구",
    "강동구",
]


def load_district_data(file_path, columns, dataset_name):
    if not file_path.exists():
        raise FileNotFoundError(
            f"{dataset_name} 전처리 결과가 없습니다: {file_path}\n"
            "해당 전처리 코드를 먼저 실행하세요."
        )

    df = pd.read_csv(file_path, encoding="utf-8-sig")
    missing_columns = [column for column in columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            f"{dataset_name} 필수 열이 없습니다: {missing_columns}\n"
            f"현재 열: {df.columns.tolist()}"
        )

    df = df[columns].copy()
    df["자치구명"] = df["자치구명"].astype("string").str.strip()

    if df["자치구명"].duplicated().any():
        duplicates = df.loc[df["자치구명"].duplicated(False), "자치구명"].tolist()
        raise ValueError(f"{dataset_name}의 자치구명이 중복되었습니다: {duplicates}")

    actual = set(df["자치구명"])
    expected = set(DISTRICTS)
    if actual != expected:
        raise ValueError(
            f"{dataset_name}의 자치구 구성이 올바르지 않습니다. "
            f"누락={sorted(expected - actual)}, 초과={sorted(actual - expected)}"
        )

    return df


def merge_one_to_one(integrated, new_data, dataset_name):
    before_count = len(integrated)
    merged = integrated.merge(
        new_data,
        on="자치구명",
        how="left",
        validate="one_to_one",
    )
    if len(merged) != before_count:
        raise ValueError(f"{dataset_name} 병합 과정에서 행 개수가 변경되었습니다.")
    return merged


def main():
    integrated = pd.DataFrame({"자치구명": DISTRICTS})

    inputs = [
        (
            "청년 인구",
            PROCESSED_DIR / "youth_population_2021_2025.csv",
            [
                "자치구명",
                "청년인구_2021",
                "청년인구_2023",
                "청년인구_2025",
            ],
        ),
        (
            "청년 1인가구",
            PROCESSED_DIR / "youth_single_household_clean_2021_2025.csv",
            [
                "자치구명",
                "청년1인가구_2021",
                "청년1인가구_2023",
                "청년1인가구_2025",
            ],
        ),
        (
            "환산월세 변화",
            PROCESSED_DIR / "rent_trend_2021_2025.csv",
            [
                "자치구명",
                "환산월세_2021_만원",
                "환산월세_2023_만원",
                "환산월세_2025_만원",
                "변화액_2021_2023_만원",
                "변화율_2021_2023_퍼센트",
                "변화액_2023_2025_만원",
                "변화율_2023_2025_퍼센트",
                "변화액_2021_2025_만원",
                "변화율_2021_2025_퍼센트",
            ],
        ),
        (
            "생활물가",
            PROCESSED_DIR / "living_price_2025_district.csv",
            ["자치구명", "생활물가지수", "분석월수", "월평균_비교품목수"],
        ),
        (
            "버스정류소",
            PROCESSED_DIR / "서울시_버스_전처리결과" / "자치구별_버스정류소_집계.csv",
            ["자치구명", "정류소수"],
        ),
        (
            "지하철역",
            PROCESSED_DIR / "서울시_지하철_전처리결과" / "자치구별_지하철역_집계.csv",
            ["자치구명", "물리적_역수", "환승역수"],
        ),
        (
            "의료시설",
            PROCESSED_DIR / "medical_facilities_clean_2025.csv",
            ["자치구명", "일상의료시설수", "종합의료시설수"],
        ),
        (
            "생활편의시설",
            PROCESSED_DIR / "retail_stores_clean_2025.csv",
            ["자치구명", "편의점수", "슈퍼마켓수", "생활편의시설수"],
        ),
    ]

    for dataset_name, file_path, columns in inputs:
        data = load_district_data(file_path, columns, dataset_name)
        integrated = merge_one_to_one(integrated, data, dataset_name)

    for year in (2021, 2023, 2025):
        population_column = f"청년인구_{year}"
        household_column = f"청년1인가구_{year}"
        concentration_column = f"청년1인가구_청년인구대비비율_{year}_퍼센트"

        if (integrated[population_column] <= 0).any():
            raise ValueError(f"{year}년 청년 인구가 0 이하인 자치구가 있습니다.")

        integrated[concentration_column] = (
            integrated[household_column] / integrated[population_column] * 100
        ).round(2)

    integrated["청년집중도_변화_2021_2025_퍼센트포인트"] = (
        integrated["청년1인가구_청년인구대비비율_2025_퍼센트"]
        - integrated["청년1인가구_청년인구대비비율_2021_퍼센트"]
    ).round(2)

    if len(integrated) != 25:
        raise ValueError(f"통합 결과가 25행이 아닙니다: {len(integrated)}행")
    if integrated["자치구명"].duplicated().any():
        raise ValueError("통합 결과에 중복 자치구가 있습니다.")
    if integrated.isna().any().any():
        missing = integrated.isna().sum()
        missing = missing[missing > 0].to_dict()
        raise ValueError(f"통합 결과에 결측치가 있습니다: {missing}")

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    integrated.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

    print("통합 데이터 생성 완료")


if __name__ == "__main__":
    main()
