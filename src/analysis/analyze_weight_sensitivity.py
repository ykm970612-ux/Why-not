from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_final_scores_2025.csv"

SCENARIO_OUTPUT_FILE = (
    PROJECT_DIR / "data" / "processed" / "weight_sensitivity_scenarios.csv"
)

RANDOM_OUTPUT_FILE = (
    PROJECT_DIR / "data" / "processed" / "weight_sensitivity_random.csv"
)

DOMAIN_COLUMNS = {
    "청년집중도": "청년집중도점수",
    "주거비": "주거비점수",
    "생활환경": "생활환경점수",
    "교통": "교통점수",
    "의료": "의료점수",
}

RANDOM_ITERATIONS = 20_000
RANDOM_SEED = 42
MIN_WEIGHT = 0.10
MAX_WEIGHT = 0.30


SCENARIOS = {
    "기준: 5개 영역 20%씩": {
        "청년집중도": 0.20,
        "주거비": 0.20,
        "생활환경": 0.20,
        "교통": 0.20,
        "의료": 0.20,
    },
    "청년집중도 30%": {
        "청년집중도": 0.30,
        "주거비": 0.175,
        "생활환경": 0.175,
        "교통": 0.175,
        "의료": 0.175,
    },
    "주거비 30%": {
        "청년집중도": 0.175,
        "주거비": 0.30,
        "생활환경": 0.175,
        "교통": 0.175,
        "의료": 0.175,
    },
    "생활환경 30%": {
        "청년집중도": 0.175,
        "주거비": 0.175,
        "생활환경": 0.30,
        "교통": 0.175,
        "의료": 0.175,
    },
    "교통 30%": {
        "청년집중도": 0.175,
        "주거비": 0.175,
        "생활환경": 0.175,
        "교통": 0.30,
        "의료": 0.175,
    },
    "의료 30%": {
        "청년집중도": 0.175,
        "주거비": 0.175,
        "생활환경": 0.175,
        "교통": 0.175,
        "의료": 0.30,
    },
}


def validate_data(df):
    required_columns = ["자치구명", *DOMAIN_COLUMNS.values()]
    missing_columns = [
        column for column in required_columns if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"민감도 분석에 필요한 열이 없습니다: {missing_columns}")

    if len(df) != 25:
        raise ValueError(f"서울 25개 자치구가 필요합니다: 현재 {len(df)}개")

    if df["자치구명"].duplicated().any():
        raise ValueError("중복된 자치구가 있습니다.")

    values = df[list(DOMAIN_COLUMNS.values())]

    if values.isna().any().any():
        raise ValueError("영역별 점수에 결측치가 있습니다.")

    if ((values < 0) | (values > 1)).any().any():
        raise ValueError("영역별 점수는 0 이상 1 이하여야 합니다.")


def calculate_scenario_scores(df, weights):
    score = pd.Series(0.0, index=df.index)

    for domain, weight in weights.items():
        column = DOMAIN_COLUMNS[domain]
        score += df[column] * weight

    return score * 100


def analyze_scenarios(df):
    rows = []

    for scenario_name, weights in SCENARIOS.items():
        scores = calculate_scenario_scores(df, weights)

        ranking = df[["자치구명"]].copy()
        ranking["점수"] = scores
        ranking = ranking.sort_values(
            ["점수", "자치구명"],
            ascending=[False, True],
        ).reset_index(drop=True)

        row = {"가중치 시나리오": scenario_name}

        for rank in range(3):
            district = ranking.loc[rank, "자치구명"]
            score = ranking.loc[rank, "점수"]

            row[f"{rank + 1}위"] = district
            row[f"{rank + 1}위_점수"] = round(score, 1)

        rows.append(row)

    return pd.DataFrame(rows)


def generate_random_weights(
    iterations,
    domain_count,
    seed,
    min_weight,
    max_weight,
):

    if min_weight * domain_count > 1:
        raise ValueError("최소 가중치 조건을 만족할 수 없습니다.")

    if max_weight * domain_count < 1:
        raise ValueError("최대 가중치 조건을 만족할 수 없습니다.")

    rng = np.random.default_rng(seed)
    accepted = []

    while sum(len(chunk) for chunk in accepted) < iterations:
        candidates = rng.dirichlet(
            np.ones(domain_count),
            size=100_000,
        )

        valid = candidates[
            (candidates >= min_weight).all(axis=1)
            & (candidates <= max_weight).all(axis=1)
        ]

        if len(valid) > 0:
            accepted.append(valid)

    return np.vstack(accepted)[:iterations]


def analyze_random_weights(df):
    score_values = df[list(DOMAIN_COLUMNS.values())].to_numpy()

    weights = generate_random_weights(
        iterations=RANDOM_ITERATIONS,
        domain_count=len(DOMAIN_COLUMNS),
        seed=RANDOM_SEED,
        min_weight=MIN_WEIGHT,
        max_weight=MAX_WEIGHT,
    )

    scores = score_values @ weights.T

    order = np.argsort(-scores, axis=0)

    top1_count = np.bincount(
        order[0],
        minlength=len(df),
    )

    top3_count = np.bincount(
        order[:3].ravel(),
        minlength=len(df),
    )

    top5_count = np.bincount(
        order[:5].ravel(),
        minlength=len(df),
    )

    bottom5_count = np.bincount(
        order[-5:].ravel(),
        minlength=len(df),
    )

    result = pd.DataFrame(
        {
            "자치구명": df["자치구명"],
            "1위_비율": top1_count / RANDOM_ITERATIONS * 100,
            "상위3위_포함비율": top3_count / RANDOM_ITERATIONS * 100,
            "상위5위_포함비율": top5_count / RANDOM_ITERATIONS * 100,
            "하위5위_포함비율": bottom5_count / RANDOM_ITERATIONS * 100,
        }
    )

    percentage_columns = [
        "1위_비율",
        "상위3위_포함비율",
        "상위5위_포함비율",
        "하위5위_포함비율",
    ]

    result[percentage_columns] = result[percentage_columns].round(1)

    return result.sort_values(
        "상위5위_포함비율",
        ascending=False,
    ).reset_index(drop=True)


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"{INPUT_FILE.name} 파일이 없습니다.")

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    validate_data(df)

    scenario_result = analyze_scenarios(df)
    random_result = analyze_random_weights(df)

    SCENARIO_OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    scenario_result.to_csv(
        SCENARIO_OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    random_result.to_csv(
        RANDOM_OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("\n가중치 시나리오별 상위 3개 자치구")
    print(scenario_result.to_string(index=False))

    print("\n무작위 가중치 분석 상위 지역")
    print(random_result.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
