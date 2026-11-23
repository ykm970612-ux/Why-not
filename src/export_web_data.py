"""웹에서 사용할 데이터를 web/data/ 로 내보낸다.

data/ 폴더는 GitHub에 올라가지 않으므로, 웹에 필요한 최종 결과만
JSON으로 변환해 web/data/ 에 저장한다.

실행: python src/export_web_data.py
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

SCORES_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_final_scores_2025.csv"
RENT_TREND_FILE = PROJECT_DIR / "data" / "processed" / "rent_trend_2021_2025.csv"
BOUNDARY_FILE = PROJECT_DIR / "data" / "raw" / "seoul.geojson.json"

OUTPUT_DIR = PROJECT_DIR / "web" / "data"


def to_records(df: pd.DataFrame) -> list[dict]:
    df = df.round(4)
    return json.loads(df.to_json(orient="records", force_ascii=False))


def write_json(data, filename: str) -> None:
    path = OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"저장: {path.relative_to(PROJECT_DIR)} ({path.stat().st_size / 1024:.1f} KB)")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 자치구별 지표·점수·순위 (25행)
    scores = pd.read_csv(SCORES_FILE, encoding="utf-8-sig")
    scores = scores.sort_values("종합순위")
    write_json(to_records(scores), "districts_2025.json")

    # 월세 구간별 변화액·변화율
    rent_trend = pd.read_csv(RENT_TREND_FILE, encoding="utf-8-sig")
    write_json(to_records(rent_trend), "rent_trend_2021_2025.json")

    # 자치구 경계 (properties.name 이 자치구명과 동일)
    with open(BOUNDARY_FILE, encoding="utf-8") as f:
        boundary = json.load(f)

    names = {feature["properties"]["name"] for feature in boundary["features"]}
    missing = set(scores["자치구명"]) - names
    if missing:
        raise ValueError(f"경계 데이터에 없는 자치구: {sorted(missing)}")

    write_json(boundary, "seoul_gu.geojson")


if __name__ == "__main__":
    main()
