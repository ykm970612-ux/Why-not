from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_final_scores_2025.csv"

OUTPUT_FILE = (
    PROJECT_DIR / "data" / "processed" / "rent_infrastructure_quadrants_2025.csv"
)


def classify_area(row, rent_median, infrastructure_median):
    rent = row["환산월세_2025_만원"]
    infrastructure = row["인프라종합점수"]

    if rent <= rent_median and infrastructure >= infrastructure_median:
        return "저비용·고인프라"

    if rent > rent_median and infrastructure >= infrastructure_median:
        return "고비용·고인프라"

    if rent <= rent_median and infrastructure < infrastructure_median:
        return "저비용·저인프라"

    return "고비용·저인프라"


def main():
    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    columns = [
        "자치구명",
        "환산월세_2025_만원",
        "인프라종합점수",
        "종합점수_100점",
        "종합순위",
    ]

    result = df[columns].copy()

    rent_median = result["환산월세_2025_만원"].median()
    infrastructure_median = result["인프라종합점수"].median()

    result["분류"] = result.apply(
        classify_area,
        axis=1,
        rent_median=rent_median,
        infrastructure_median=infrastructure_median,
    )

    result["월세_중앙값"] = rent_median
    result["인프라_중앙값"] = infrastructure_median

    result = result.sort_values(["분류", "종합순위"]).reset_index(drop=True)

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print(f"\n분류표 생성 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
