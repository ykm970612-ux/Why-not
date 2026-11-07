import pandas as pd
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"


def main():

    # 파일이 없는경우 종료.
    if not (PROCESSED_DIR / "rent_2021_2025_district.csv").exists():
        raise FileNotFoundError("rent_2021_2025_district.csv 파일이 없습니다. ")

    df = pd.read_csv(
        PROCESSED_DIR / "rent_2021_2025_district.csv", encoding="utf-8-sig"
    )

    # 연도를 열로 변환
    trend = df.pivot(
        index="자치구명", columns="기준연도", values="환산월세_중앙값_만원"
    ).reset_index()

    # 컬럼 이름 정리
    trend.columns.name = None

    trend = trend.rename(
        columns={
            2021: "환산월세_2021_만원",
            2023: "환산월세_2023_만원",
            2025: "환산월세_2025_만원",
        }
    )

    # 2021년 → 2023년 변화
    trend["변화액_2021_2023_만원"] = (
        trend["환산월세_2023_만원"] - trend["환산월세_2021_만원"]
    )

    trend["변화율_2021_2023_퍼센트"] = (
        trend["변화액_2021_2023_만원"] / trend["환산월세_2021_만원"] * 100
    )

    # 2023년 → 2025년 변화
    trend["변화액_2023_2025_만원"] = (
        trend["환산월세_2025_만원"] - trend["환산월세_2023_만원"]
    )

    trend["변화율_2023_2025_퍼센트"] = (
        trend["변화액_2023_2025_만원"] / trend["환산월세_2023_만원"] * 100
    )

    # 2021년 → 2025년 전체 변화
    trend["변화액_2021_2025_만원"] = (
        trend["환산월세_2025_만원"] - trend["환산월세_2021_만원"]
    )

    trend["변화율_2021_2025_퍼센트"] = (
        trend["변화액_2021_2025_만원"] / trend["환산월세_2021_만원"] * 100
    )

    # 소수점 둘째 자리까지 반올림

    numeric_columns = trend.columns.drop("자치구명")

    trend[numeric_columns] = trend[numeric_columns].round(2)

    # 자치구명 순서로 정렬
    trend = trend.sort_values("자치구명").reset_index(drop=True)

    # 결과 저장
    trend.to_csv(
        PROCESSED_DIR / "rent_trend_2021_2025.csv", index=False, encoding="utf-8-sig"
    )

    print("환산월세 변화율 계산 완료")


if __name__ == "__main__":
    main()
