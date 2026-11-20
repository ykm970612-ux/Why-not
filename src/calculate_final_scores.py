from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_normalized_2025.csv"

OUTPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_final_scores_2025.csv"


INDICATOR_COLUMNS = [
    "청년1인가구_LQ_2025_정규화",
    "환산월세_2025_정규화",
    "월세변화율_정규화",
    "생활물가지수_정규화",
    "생활편의시설수_정규화",
    "버스정류소수_정규화",
    "물리적_역수_정규화",
    "일상의료시설수_정규화",
    "종합의료시설수_정규화",
]


INFRASTRUCTURE_COLUMNS = [
    "생활편의시설수_정규화",
    "버스정류소수_정규화",
    "물리적_역수_정규화",
    "일상의료시설수_정규화",
    "종합의료시설수_정규화",
]


DOMAIN_SCORE_COLUMNS = [
    "청년집중도점수",
    "주거비점수",
    "생활환경점수",
    "교통점수",
    "의료점수",
]


def calculate_scores(df):
    missing_columns = [column for column in INDICATOR_COLUMNS if column not in df.columns]
    if missing_columns:
        raise ValueError(f"최종점수 산출에 필요한 열이 없습니다: {missing_columns}")

    result = df.copy()

    for column in INDICATOR_COLUMNS:
        result[column] = pd.to_numeric(result[column], errors="raise")

    if result[INDICATOR_COLUMNS].isna().any().any():
        raise ValueError("최종점수 산출 지표에 결측치가 있습니다.")

    if ((result[INDICATOR_COLUMNS] < 0) | (result[INDICATOR_COLUMNS] > 1)).any().any():
        raise ValueError("정규화 지표는 0 이상 1 이하여야 합니다.")

    result["청년집중도점수"] = result["청년1인가구_LQ_2025_정규화"]

    result["주거비점수"] = result[
        [
            "환산월세_2025_정규화",
            "월세변화율_정규화",
        ]
    ].mean(axis=1)

    result["생활환경점수"] = result[
        [
            "생활물가지수_정규화",
            "생활편의시설수_정규화",
        ]
    ].mean(axis=1)

    result["교통점수"] = result[
        [
            "버스정류소수_정규화",
            "물리적_역수_정규화",
        ]
    ].mean(axis=1)

    result["의료점수"] = result[
        [
            "일상의료시설수_정규화",
            "종합의료시설수_정규화",
        ]
    ].mean(axis=1)

    result["인프라종합점수"] = result[INFRASTRUCTURE_COLUMNS].mean(axis=1)

    # 5개 영역에 각각 20%의 동일 가중치 적용
    result["종합점수"] = result[DOMAIN_SCORE_COLUMNS].mean(axis=1)

    result["종합점수_100점"] = (result["종합점수"] * 100).round(2)

    result["종합순위"] = (
        result["종합점수"].rank(method="min", ascending=False).astype(int)
    )

    result = result.sort_values(["종합순위", "자치구명"]).reset_index(drop=True)

    return result


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"정규화 통합표가 없습니다: {INPUT_FILE}\n"
            "create_normalized_table.py를 먼저 실행하세요."
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    if len(df) != 25:
        raise ValueError(f"정규화 통합표가 25행이 아닙니다: {len(df)}행")

    if df["자치구명"].duplicated().any():
        raise ValueError("정규화 통합표에 중복 자치구가 있습니다.")

    result = calculate_scores(df)

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("최종 종합점수 생성 완료")


if __name__ == "__main__":
    main()
