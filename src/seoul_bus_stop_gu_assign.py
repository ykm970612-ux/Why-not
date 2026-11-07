from pathlib import Path
import argparse
import json
import sys
import pandas as pd
import geopandas as gpd

def find_col(columns, candidates):
    # 데이터 공백 제거 작업
    normalized = {str(c).replace(" ", "").strip().lower(): c for c in columns}
    for cand in candidates:
        key = cand.replace(" ", "").strip().lower()
        if key in normalized:
            return normalized[key]
    return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--boundary", default="seoul.geojson.json",
                        help="자치구 경계 GeoJSON 경로")
    parser.add_argument("--bus", default="bus_stops_2025_seoul.csv",
                        help="버스정류소 Excel/CSV 경로")
    parser.add_argument("--outdir", default="서울시_버스정류소_전처리결과",
                        help="결과 저장 폴더")
    parser.add_argument("--sheet", default=0, help="Excel 시트명 또는 번호")
    args = parser.parse_args()

    boundary_path = Path(args.boundary)
    bus_path = Path(args.bus)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not boundary_path.exists():
        raise FileNotFoundError(f"경계 파일을 찾을 수 없습니다: {boundary_path}")
    if not bus_path.exists():
        raise FileNotFoundError(f"정류소 파일을 찾을 수 없습니다: {bus_path}")

    #자치구 경계 읽기, 필수 속성 확인
    districts = gpd.read_file(boundary_path)
    if districts.crs is None:
        districts = districts.set_crs("EPSG:4326")
    else:
        districts = districts.to_crs("EPSG:4326")

    name_col = find_col(districts.columns, ["name", "SIG_KOR_NM", "자치구명"])
    code_col = find_col(districts.columns, ["code", "SIG_CD", "자치구코드"])
    if name_col is None:
        raise ValueError(f"경계 파일에서 자치구명 컬럼을 찾지 못했습니다. 컬럼: {list(districts.columns)}")
    if code_col is None:
        raise ValueError(f"경계 파일에서 자치구 코드 컬럼을 찾지 못했습니다. 컬럼: {list(districts.columns)}")

    districts = districts[[code_col, name_col, "geometry"]].copy()
    districts = districts.rename(columns={code_col: "자치구코드", name_col: "자치구"})
    districts["자치구코드"] = districts["자치구코드"].astype(str).str.replace(r"\.0$", "", regex=True)
    districts = districts.drop_duplicates(subset=["자치구코드"])
    if len(districts) != 25:
        raise ValueError(f"자치구 경계가 25개가 아닙니다. 현재 {len(districts)}개입니다.")
    if districts.geometry.is_empty.any() or districts.geometry.isna().any():
        raise ValueError("경계 파일에 비어 있거나 누락된 geometry가 있습니다.")

    # 버스정류소 파일 읽기
    if bus_path.suffix.lower() in [".xlsx", ".xls"]:
        bus = pd.read_excel(bus_path, sheet_name=args.sheet)
    elif bus_path.suffix.lower() == ".csv":
        try:
            bus = pd.read_csv(bus_path, encoding="utf-8-sig")
        except UnicodeDecodeError:
            bus = pd.read_csv(bus_path, encoding="cp949")
    else:
        raise ValueError("정류소 입력은 xlsx, xls 또는 csv 파일이어야 합니다.")

    x_col = find_col(bus.columns, ["X좌표", "경도", "longitude", "lon", "x"])
    y_col = find_col(bus.columns, ["Y좌표", "위도", "latitude", "lat", "y"])
    if x_col is None or y_col is None:
        raise ValueError(f"좌표 컬럼을 찾지 못했습니다. 현재 컬럼: {list(bus.columns)}")

    # 고유 행 ID 부여
    bus = bus.copy().reset_index(drop=True)
    bus.insert(0, "원본행번호", range(1, len(bus) + 1))
    bus[x_col] = pd.to_numeric(bus[x_col], errors="coerce")
    bus[y_col] = pd.to_numeric(bus[y_col], errors="coerce")

    valid_mask = (
        bus[x_col].between(124, 132) &
        bus[y_col].between(33, 39)
    )
    valid = bus.loc[valid_mask].copy()
    invalid = bus.loc[~valid_mask].copy()
    points = gpd.GeoDataFrame(
        valid,
        geometry=gpd.points_from_xy(valid[x_col], valid[y_col]),
        crs="EPSG:4326"
    )

    joined = gpd.sjoin(
        points,
        districts,
        how="left",
        predicate="within"
    )

    unmatched_mask = joined["자치구"].isna()
    if unmatched_mask.any():
        boundary_points = points.loc[points["원본행번호"].isin(
            joined.loc[unmatched_mask, "원본행번호"]
        )]
        if not boundary_points.empty:
            boundary_join = gpd.sjoin(
                boundary_points,
                districts,
                how="left",
                predicate="intersects"
            )
            
            boundary_join = (
                boundary_join.sort_values(["원본행번호", "자치구코드"])
                .drop_duplicates(subset=["원본행번호"], keep="first")
            )
            replace_map = boundary_join.set_index("원본행번호")[["자치구코드", "자치구"]]
            for col in ["자치구코드", "자치구"]:
                joined.loc[unmatched_mask, col] = (
                    joined.loc[unmatched_mask, "원본행번호"].map(replace_map[col])
                )

    joined = (
        joined.sort_values(["원본행번호", "자치구코드"])
        .drop_duplicates(subset=["원본행번호"], keep="first")
    )
    matched = joined.loc[joined["자치구"].notna()].copy()
    unmatched = joined.loc[joined["자치구"].isna()].copy()

    # 자치구별 집계 작업
    counts = matched.groupby(["자치구코드", "자치구"]).size().rename("정류소수").reset_index()
    summary = districts[["자치구코드", "자치구"]].merge(
        counts, on=["자치구코드", "자치구"], how="left"
    )
    summary["정류소수"] = summary["정류소수"].fillna(0).astype(int)
    summary = summary.sort_values("자치구코드").reset_index(drop=True)

    # 결과 저장
    detail_cols = [c for c in bus.columns if c != "geometry"]
    detail = pd.DataFrame(matched.drop(columns="geometry"))[detail_cols + ["자치구코드", "자치구"]]
    unmatched_detail = pd.DataFrame(unmatched.drop(columns="geometry"))[detail_cols]
    invalid_detail = invalid.copy()

    detail.to_csv(outdir / "버스정류소_자치구분류.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(outdir / "자치구별_버스정류소_집계.csv", index=False, encoding="utf-8-sig")
    unmatched_detail.to_csv(outdir / "자치구_미분류_정류소.csv", index=False, encoding="utf-8-sig")
    invalid_detail.to_csv(outdir / "좌표오류_정류소.csv", index=False, encoding="utf-8-sig")

    with pd.ExcelWriter(outdir / "버스정류소_자치구별_전처리결과.xlsx", engine="openpyxl") as writer:
        detail.to_excel(writer, sheet_name="정류소별_분류", index=False)
        summary.to_excel(writer, sheet_name="자치구별_집계", index=False)
        unmatched_detail.to_excel(writer, sheet_name="자치구_미분류", index=False)
        invalid_detail.to_excel(writer, sheet_name="좌표오류", index=False)

    if not matched.empty:
        matched[["원본행번호", "자치구코드", "자치구", "geometry"]].to_file(
            outdir / "버스정류소_자치구분류.geojson",
            driver="GeoJSON", encoding="utf-8"
        )

    report = {
        "경계_자치구수": int(len(districts)),
        "원본_정류소수": int(len(bus)),
        "좌표정상_정류소수": int(len(valid)),
        "좌표오류_정류소수": int(len(invalid)),
        "자치구_분류성공": int(len(matched)),
        "자치구_미분류": int(len(unmatched)),
        "자치구별_집계합계": int(summary["정류소수"].sum()),
        "경계파일": str(boundary_path),
        "정류소파일": str(bus_path),
        "좌표계": "EPSG:4326 (경도/위도)"
    }
    with open(outdir / "전처리_검증요약.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n결과 저장 위치: {outdir.resolve()}")

if __name__ == "__main__":
    main()
