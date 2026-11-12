from .healthnconv_preprocess_facilities import (
    DISTRICTS,
    MEDICAL_INDICATORS,
    ROOT,
    count,
    district,
    read_csv,
    require,
    require_columns,
    write_csv,
)

PROCESSED_DIR = ROOT / "data" / "processed"
INPUTS = {
    "medical_facilities_clean_2025.csv": tuple(MEDICAL_INDICATORS),
    "retail_stores_clean_2025.csv": ("생활편의시설수",),
}
OUTPUT = PROCESSED_DIR / "healthnconv_minmax_2025.csv"


def load_indicators(path, columns):
    rows, _, _ = read_csv(path)
    require_columns(rows, ("자치구명", "기준연도", *columns))
    by_district = {}
    for row in rows:
        name = district(row["자치구명"])
        require(name not in by_district, f"{path.name}: 중복 자치구 {name}")
        require(row["기준연도"].strip() == "2025", f"{path.name}: {name} 기준연도 오류")
        by_district[name] = {column: count(row[column]) for column in columns}
    missing = sorted(set(DISTRICTS) - by_district.keys())
    require(not missing, f"{path.name}: 누락 자치구 {missing}")
    return by_district


def min_max(values):
    low, high = min(values), max(values)
    if low == high:
        return [0.0] * len(values)
    return [(value - low) / (high - low) for value in values]


def main():
    result = [{"자치구명": name, "기준연도": 2025} for name in DISTRICTS]
    for filename, columns in INPUTS.items():
        data = load_indicators(PROCESSED_DIR / filename, columns)
        for column in columns:
            normalized = min_max([data[name][column] for name in DISTRICTS])
            for row, value in zip(result, normalized):
                row[f"{column}_정규화"] = round(value, 4)

    write_csv(OUTPUT, result)
    print(f"{len(result)}개 자치구 정규화 결과 저장: {OUTPUT}")


if __name__ == "__main__":
    main()
