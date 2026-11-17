import argparse
from pathlib import Path
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib import font_manager, colors, colormaps
from shapely.ops import polylabel

MAPS = [
    ("종합점수_100점", "01_final_score.png", "최종 종합점수 (100점)", "YlGnBu", "{:.1f}", "점수"),
    ("청년1인가구_LQ_2025", "02_youth_lq.png", "청년 1인가구 LQ (2025)", "YlGn", "{:.2f}", "LQ"),
    ("환산월세_2025_만원", "03_monthly_rent.png", "환산월세 (2025)", "OrRd", "{:.1f}", "만원"),
    ("인프라종합점수", "04_infrastructure.png", "생활 인프라 종합점수", "PuBuGn", "{:.2f}", "정규화 점수 (0~1)"),
]

def font_setup():
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in ("NanumGothic", "Noto Sans CJK KR", "Malgun Gothic", "AppleGothic"):
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False

def load(scores, boundary):
    df = pd.read_csv(scores, encoding="utf-8-sig")
    needed = ["자치구명"] + [m[0] for m in MAPS]
    missing = sorted(set(needed) - set(df.columns))
    if missing:
        raise ValueError(f"최종점수표에 필요한 열이 없습니다: {missing}")
    if len(df) != 25 or df["자치구명"].duplicated().any():
        raise ValueError("최종점수표는 서울 25개 구가 각 1행이어야 합니다.")
    geo = gpd.read_file(boundary)
    name_col = next((x for x in ("자치구명", "name", "SIG_KOR_NM") if x in geo.columns), None)
    if name_col is None:
        raise ValueError("경계 파일에서 자치구 이름 열을 찾지 못했습니다.")
    geo["자치구명"] = geo[name_col].astype(str).str.strip()
    geo = geo[geo["자치구명"].isin(df["자치구명"])][["자치구명", "geometry"]]
    geo = geo.dissolve(by="자치구명", as_index=False)
    if geo.crs is None:
        raise ValueError("경계 파일 CRS가 없습니다.")
    merged = geo.to_crs(epsg=5179).merge(df[needed], on="자치구명", how="left", validate="one_to_one")
    if len(merged) != 25 or merged[needed[1:]].isna().any().any():
        raise ValueError("25개 구 결합 실패 또는 점수 결측 발생")
    return merged

def draw(geo, spec, out):
    col, filename, title, cmap, number_format, legend_label = spec
    fig, ax = plt.subplots(figsize=(11, 10), dpi=180)
    vals = pd.to_numeric(geo[col])
    norm = colors.Normalize(vmin=vals.min(), vmax=vals.max())
    geo.plot(column=col, cmap=cmap, linewidth=0.85, edgecolor="#ffffff",
             legend=True, legend_kwds={"label":legend_label, "shrink":0.62}, ax=ax)
    palette = colormaps[cmap]
    for _, row in geo.iterrows():
        geom = row.geometry
        if geom.geom_type == "MultiPolygon":
            geom = max(geom.geoms, key=lambda x: x.area)
        point = polylabel(geom, tolerance=30)
        rgba = palette(norm(row[col]))
        brightness = 0.2126*rgba[0] + 0.7152*rgba[1] + 0.0722*rgba[2]
        color = "#172635" if brightness > 0.54 else "#ffffff"
        stroke = "#ffffff" if brightness > 0.54 else "#172635"
        label = f"{row['자치구명']}\n{number_format.format(row[col])}"
        ax.annotate(label, (point.x, point.y), ha="center", va="center",
                    fontsize=7.5, fontweight="bold", color=color, linespacing=1.25,
                    path_effects=[pe.withStroke(linewidth=1.2, foreground=stroke)])
    ax.set_title(title, fontsize=16, weight="bold", pad=18)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(out / filename, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("생성:", out / filename)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scores", type=Path, default=Path("data/processed/seoul_youth_final_scores_2025.csv"))
    p.add_argument("--boundary", type=Path, default=Path("data/raw/seoul.geojson.json"))
    p.add_argument("--out", type=Path, default=Path("outputs/charts"))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    font_setup()
    geo = load(args.scores, args.boundary)
    for spec in MAPS:
        draw(geo, spec, args.out)
    print("지도 생성 완료")

if __name__ == "__main__":
    main()
