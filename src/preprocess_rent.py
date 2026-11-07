from pathlib import Path

import pandas as pd

# 파일경로 생성.
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

# 보증금 연 환산율 5%
CONVERSION_RATE = 0.05


def preprocess_rent(file_path, year, encoding="cp949"):

    # 파일이 없는경우 종료.
    if not (PROCESSED_DIR / file_path).exists():
        raise FileNotFoundError(f"{file_path.name} 파일이 없습니다.")

    df = pd.read_csv(file_path, encoding=encoding, low_memory=False)

    # 숫자형으로 변환.
    df["계약일"] = pd.to_numeric(df["계약일"], errors="coerce")

    df["임대면적"] = pd.to_numeric(df["임대면적"], errors="coerce")

    df["보증금(만원)"] = pd.to_numeric(df["보증금(만원)"], errors="coerce")

    df["임대료(만원)"] = pd.to_numeric(df["임대료(만원)"], errors="coerce")

    # 계약일에서 계약연도 추출 ex) 20250327 // 10000 = 2025

    df["계약연도"] = df["계약일"] // 10000

    df_2 = df[
        (df["계약연도"] == year)
        & (df["전월세구분"] == "월세")
        & (df["임대면적"] > 0)
        & (df["임대면적"] <= 60)
        & (df["보증금(만원)"] >= 0)
        & (df["임대료(만원)"] > 0)
    ].copy()

    # 결측치 제거
    df_2 = df_2.dropna(subset=["자치구명", "임대면적", "보증금(만원)", "임대료(만원)"])

    # 보증금 월 환산율 5%
    df_2["환산월세_만원"] = (
        df_2["임대료(만원)"] + df_2["보증금(만원)"] * CONVERSION_RATE / 12
    )

    # 자치구별 중앙값, 계약 건수 계산
    df_3 = (
        df_2.groupby("자치구명", as_index=False)
        .agg(
            월세_계약건수=("임대료(만원)", "count"),
            월세_중앙값_만원=("임대료(만원)", "median"),
            보증금_중앙값_만원=("보증금(만원)", "median"),
            환산월세_중앙값_만원=("환산월세_만원", "median"),
            임대면적_중앙값_m2=("임대면적", "median"),
        )
        .sort_values("자치구명")
        .reset_index(drop=True)
    )

    # 기준연도 추가
    df_3.insert(1, "기준연도", year)

    # 소수점 2자리 까지 반올림
    df_3[
        [
            "월세_중앙값_만원",
            "보증금_중앙값_만원",
            "환산월세_중앙값_만원",
            "임대면적_중앙값_m2",
        ]
    ] = df_3[
        [
            "월세_중앙값_만원",
            "보증금_중앙값_만원",
            "환산월세_중앙값_만원",
            "임대면적_중앙값_m2",
        ]
    ].round(
        2
    )

    return df_3


def main():

    # 결과 폴더 생성, 없으면 생성
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # 전처리
    rent_2021 = preprocess_rent(RAW_DIR / "rent_transactions_2021_seoul.txt", 2021)

    rent_2023 = preprocess_rent(
        RAW_DIR / "rent_transactions_2023_seoul.csv", 2023, encoding="utf-8-sig"
    )

    rent_2025 = preprocess_rent(RAW_DIR / "rent_transactions_2025_seoul.csv", 2025)

    # 세 연도 결과 합치기
    combined = pd.concat([rent_2021, rent_2023, rent_2025], ignore_index=True)

    combined.to_csv(
        PROCESSED_DIR / "rent_2021_2025_district.csv", index=False, encoding="utf-8-sig"
    )

    print("월세 데이터 전처리 완료")


if __name__ == "__main__":
    main()
