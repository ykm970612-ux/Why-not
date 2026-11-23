"""웹에서 사용할 데이터를 web/data/data.js 로 내보낸다.

data/ 폴더는 GitHub에 올라가지 않으므로, 웹에 필요한 최종 결과만 모아 저장한다.
JSON 파일을 fetch 하면 index.html 을 파일로 바로 열 때(file://) 브라우저가 막기 때문에,
데이터를 window.WEB_DATA 에 담는 JS 파일로 만들어 <script> 로 불러오게 한다.

실행: python src/export_web_data.py
"""

import json
from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]

SCORES_FILE = PROJECT_DIR / "data" / "processed" / "seoul_youth_final_scores_2025.csv"
RENT_TREND_FILE = PROJECT_DIR / "data" / "processed" / "rent_trend_2021_2025.csv"
BOUNDARY_FILE = PROJECT_DIR / "data" / "raw" / "seoul.geojson.json"

OUTPUT_FILE = PROJECT_DIR / "web" / "data" / "data.js"


def to_records(df: pd.DataFrame) -> list[dict]:
    df = df.round(4)
    return json.loads(df.to_json(orient="records", force_ascii=False))


def main() -> None:
    # 자치구별 지표·점수·순위 (25행)
    scores = pd.read_csv(SCORES_FILE, encoding="utf-8-sig")
    scores = scores.sort_values("종합순위")

    # 월세 구간별 변화액·변화율
    rent_trend = pd.read_csv(RENT_TREND_FILE, encoding="utf-8-sig")

    # 자치구 경계 (properties.name 이 자치구명과 동일)
    with open(BOUNDARY_FILE, encoding="utf-8") as f:
        boundary = json.load(f)

    names = {feature["properties"]["name"] for feature in boundary["features"]}
    missing = set(scores["자치구명"]) - names
    if missing:
        raise ValueError(f"경계 데이터에 없는 자치구: {sorted(missing)}")

    data = {
        "districts": to_records(scores),
        "rentTrend": to_records(rent_trend),
        "boundary": boundary,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("// src/export_web_data.py 로 생성한 파일입니다. 직접 수정하지 마세요.\n")
        f.write("window.WEB_DATA = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"저장: {OUTPUT_FILE.relative_to(PROJECT_DIR)} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
