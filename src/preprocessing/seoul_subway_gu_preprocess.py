from pathlib import Path
import json
import re
import pandas as pd

# 사용할 자료 지정
PROJECT_DIR = Path(__file__).resolve().parents[2]

STATION_CSV = PROJECT_DIR / "data" / "raw" / "subway_stations_2025_seoulmetro.csv"

BOUNDARY_GEOJSON = PROJECT_DIR / "data" / "raw" / "seoul.geojson.json"

OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / "서울시_지하철_전처리결과"

REQUIRED_COLUMNS = ["역번호", "호선", "역명", "도로명주소"]


def read_csv_auto(path: Path) -> pd.DataFrame:
    errors = []
    for enc in ("cp949", "euc-kr", "utf-8-sig", "utf-8"):
        try:
            return pd.read_csv(path, encoding=enc, dtype=str)
        except Exception as exc:
            errors.append(f"{enc}: {exc}")
    raise RuntimeError("CSV 인코딩을 판별하지 못했습니다.\n" + "\n".join(errors))


def load_gu_boundary(path: Path):
    with path.open("r", encoding="utf-8") as f:
        geo = json.load(f)
    features = geo.get("features", [])
    rows = []
    for ft in features:
        props = ft.get("properties", {})
        name = props.get("name")
        code = props.get("code")
        if name and code:
            rows.append(
                {"자치구명": str(name).strip(), "자치구코드": str(code).strip()}
            )
    boundary = pd.DataFrame(rows).drop_duplicates()
    if len(boundary) != 25:
        raise ValueError(
            f"경계 GeoJSON에서 자치구가 25개가 아닙니다. 현재 {len(boundary)}개"
        )
    if boundary["자치구명"].duplicated().any():
        raise ValueError("경계 GeoJSON에 중복 자치구명이 있습니다.")
    return boundary, geo.get(
        "base", features[0].get("properties", {}).get("base") if features else None
    )


def extract_gu(address):
    if pd.isna(address):
        return None
    text = str(address).strip()

    # 서울 주소인지 확인 ? 서울특별시/서울시

    if not (text.startswith("서울특별시") or text.startswith("서울시")):
        return None
    match = re.search(r"(?:서울특별시|서울시)\s*([가-힣]+구)", text)
    return match.group(1) if match else None


def normalize_station_name(name):
    if pd.isna(name):
        return ""
    # 역명 끝 공백 정리
    value = re.sub(r"\s+", "", str(name))
    return value


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for p in (STATION_CSV, BOUNDARY_GEOJSON):
        if not p.exists():
            raise FileNotFoundError(
                f"입력 파일을 찾을 수 없습니다: {p}\n"
                "입력 파일을 data/raw 폴더에 배치하세요."
            )

    boundary, boundary_base = load_gu_boundary(BOUNDARY_GEOJSON)
    gu_names = set(boundary["자치구명"])

    df = read_csv_auto(STATION_CSV)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV에 필요한 컬럼이 없습니다: {missing}\n현재 컬럼: {df.columns.tolist()}"
        )
    # 원자료 보존 및 문자열 정리
    df = df.copy()
    for col in REQUIRED_COLUMNS:
        df[col] = df[col].astype("string").str.strip()

    df["주소에서_추출한_자치구명"] = df["도로명주소"].apply(extract_gu)
    df["자치구명"] = df["주소에서_추출한_자치구명"]
    df["자치구코드"] = df["자치구명"].map(
        boundary.set_index("자치구명")["자치구코드"].to_dict()
    )
    df["분류상태"] = "정상"
    df.loc[df["주소에서_추출한_자치구명"].isna(), "분류상태"] = (
        "서울 외 지역 또는 주소에서 자치구 확인 불가"
    )
    df.loc[
        df["주소에서_추출한_자치구명"].notna()
        & ~df["주소에서_추출한_자치구명"].isin(gu_names),
        "분류상태",
    ] = "경계 GeoJSON 자치구 목록과 불일치"

    df["역명_정규화"] = df["역명"].apply(normalize_station_name)
    df["역번호"] = df["역번호"].astype("string").str.strip()
    df["호선"] = df["호선"].astype("string").str.strip()
    # 물리적 역 단위 : 같은 자치구 + 정규화 역명은 환승역으로 보고 1개로 집계
    valid = df[df["분류상태"] == "정상"].copy()
    physical_rows = []
    for (gu, station), group in valid.groupby(
        ["자치구명", "역명_정규화"], dropna=False, sort=True
    ):
        first = group.iloc[0]
        physical_rows.append(
            {
                "자치구명": gu,
                "자치구코드": first["자치구코드"],
                "역명": first["역명"],
                "역명_정규화": station,
                "노선수": group["호선"].nunique(),
                "노선목록": ", ".join(
                    sorted(group["호선"].dropna().unique(), key=lambda x: (len(x), x))
                ),
                "역번호목록": ", ".join(group["역번호"].dropna().unique()),
                "주소": first["도로명주소"],
                "원자료행수": len(group),
                "환승역여부": "예" if group["호선"].nunique() > 1 else "아니오",
            }
        )
    physical = pd.DataFrame(
        physical_rows,
        columns=[
            "자치구명",
            "자치구코드",
            "역명",
            "역명_정규화",
            "노선수",
            "노선목록",
            "역번호목록",
            "주소",
            "원자료행수",
            "환승역여부",
        ],
    )

    # 자치구별 0건도 포함 출력
    gu_summary = boundary[["자치구명", "자치구코드"]].copy()
    physical_counts = physical.groupby("자치구명").size().rename("물리적_역수")
    line_record_counts = valid.groupby("자치구명").size().rename("노선별_역자료_행수")
    transfer_counts = (
        physical[physical["환승역여부"] == "예"]
        .groupby("자치구명")
        .size()
        .rename("환승역수")
        if not physical.empty
        else pd.Series(dtype="int64", name="환승역수")
    )
    gu_summary = gu_summary.merge(physical_counts, on="자치구명", how="left")
    gu_summary = gu_summary.merge(line_record_counts, on="자치구명", how="left")
    gu_summary = gu_summary.merge(transfer_counts, on="자치구명", how="left")
    for col in ("물리적_역수", "노선별_역자료_행수", "환승역수"):
        gu_summary[col] = gu_summary[col].fillna(0).astype(int)

    line_summary = (
        valid.groupby(["자치구명", "호선"])
        .size()
        .reset_index(name="노선별_역자료_행수")
        .sort_values(["자치구명", "호선"])
    )

    cross_gu = (
        valid.groupby("역명_정규화")["자치구명"]
        .nunique()
        .loc[lambda s: s > 1]
        .index.tolist()
    )
    review = valid[valid["역명_정규화"].isin(cross_gu)].sort_values(
        ["역명_정규화", "자치구명"]
    )

    unmatched = df[df["분류상태"] != "정상"].copy()
    duplicates = df[df.duplicated(subset=["역번호", "호선", "역명"], keep=False)].copy()
    full_duplicates = df[
        df.duplicated(subset=read_csv_auto(STATION_CSV).columns.tolist(), keep=False)
    ].copy()

    # 저장
    df.to_csv(
        OUTPUT_DIR / "지하철역_노선별_자치구분류.csv", index=False, encoding="utf-8-sig"
    )
    physical.to_csv(
        OUTPUT_DIR / "지하철역_환승중복제거_물리적역.csv",
        index=False,
        encoding="utf-8-sig",
    )
    gu_summary.to_csv(
        OUTPUT_DIR / "자치구별_지하철역_집계.csv", index=False, encoding="utf-8-sig"
    )
    unmatched.to_csv(
        OUTPUT_DIR / "자치구_미분류_검토.csv", index=False, encoding="utf-8-sig"
    )

    with pd.ExcelWriter(
        OUTPUT_DIR / "지하철역_자치구별_전처리결과.xlsx", engine="openpyxl"
    ) as writer:
        gu_summary.to_excel(writer, sheet_name="자치구별_역수", index=False)
        physical.to_excel(writer, sheet_name="물리적_역목록", index=False)
        df.to_excel(writer, sheet_name="노선별_원자료분류", index=False)
        line_summary.to_excel(writer, sheet_name="자치구별_노선별", index=False)
        unmatched.to_excel(writer, sheet_name="미분류_검토", index=False)
        review.to_excel(writer, sheet_name="동일역명_다른구_검토", index=False)
        duplicates.to_excel(writer, sheet_name="원자료중복_검토", index=False)
        full_duplicates.to_excel(writer, sheet_name="전체행중복_검토", index=False)

    report = {
        "경계기준일": boundary_base,
        "역번호_호선_역명_중복행수": int(len(duplicates)),
        "원자료_전체행중복행수": int(len(full_duplicates)),
        "경계_자치구수": int(len(boundary)),
        "원자료_행수": int(len(df)),
        "정상분류_노선별_행수": int((df["분류상태"] == "정상").sum()),
        "미분류_행수": int((df["분류상태"] != "정상").sum()),
        "물리적_역수_환승중복제거": int(len(physical)),
        "환승역수": (
            int((physical["환승역여부"] == "예").sum()) if not physical.empty else 0
        ),
        "역명이다른자치구에나타나는검토역명수": int(len(cross_gu)),
        "입력파일": STATION_CSV.name,
        "경계파일": BOUNDARY_GEOJSON.name,
    }
    print("전처리 완료")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"결과 폴더: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
