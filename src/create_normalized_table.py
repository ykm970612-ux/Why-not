from pathlib import Path

import pandas as pd

from indicators.bus_subway_minmax import add_minmax_columns
from indicators.healthnconv_normalize_facilities import (
    add_healthnconv_indicators,
)
from indicators.living_price import add_living_price_indicator
from indicators.rent import add_rent_indicators
from indicators.youth_single_household import (
    add_youth_single_household_lq,
)

PROJECT_DIR = Path(__file__).resolve().parents[1]

INPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_integrated_2025.csv"

OUTPUT_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_normalized_2025.csv"


NORMALIZED_COLUMNS = [
    "청년1인가구_LQ_2025_정규화",
    "환산월세_2025_정규화",
    "월세변화율_정규화",
    "생활물가지수_정규화",
    "버스정류소수_정규화",
    "물리적_역수_정규화",
    "일상의료시설수_정규화",
    "종합의료시설수_정규화",
    "생활편의시설수_정규화",
]


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"통합 데이터 파일이 없습니다: {INPUT_FILE}\n"
            "integrate_district_data.py를 먼저 실행하세요."
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    if len(df) != 25:
        raise ValueError(f"통합 데이터가 25행이 아닙니다: {len(df)}행")

    if df["자치구명"].duplicated().any():
        raise ValueError("통합 데이터에 중복 자치구가 있습니다.")

    # 청년 1인가구 LQ 산출
    result = add_youth_single_household_lq(df)

    # 환산월세 정규화
    result = add_rent_indicators(result)

    # 생활물가지수 정규화
    result = add_living_price_indicator(result)

    # 버스정류소·지하철역 정규화
    result = add_minmax_columns(result)

    # 의료·생활편의시설 정규화
    result = add_healthnconv_indicators(result)

    # 2021년과 2023년 LQ 정규화 값은 종합점수에서 사용하지 않음
    result = result.drop(
        columns=[
            "청년1인가구_LQ_2021_정규화",
            "청년1인가구_LQ_2023_정규화",
        ],
        errors="ignore",
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("정규화 통합표 생성 완료")


if __name__ == "__main__":
    main()
