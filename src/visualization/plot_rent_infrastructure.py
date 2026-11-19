from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from scipy.stats import spearmanr

PROJECT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = (
    PROJECT_DIR / "data" / "processed" / "rent_infrastructure_quadrants_2025.csv"
)

OUTPUT_FILE = PROJECT_DIR / "outputs" / "charts" / "rent_infrastructure_quadrant.png"


def setup_font():
    available_fonts = {font.name for font in font_manager.fontManager.ttflist}

    font_candidates = [
        "Malgun Gothic",
        "NanumGothic",
        "Noto Sans CJK KR",
        "AppleGothic",
    ]

    for font_name in font_candidates:
        if font_name in available_fonts:
            plt.rcParams["font.family"] = font_name
            break

    plt.rcParams["axes.unicode_minus"] = False


def main():
    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    rent_median = df["월세_중앙값"].iloc[0]
    infrastructure_median = df["인프라_중앙값"].iloc[0]

    # 스피어맨 상관계수
    correlation, p_value = spearmanr(
        df["환산월세_2025_만원"],
        df["인프라종합점수"],
    )

    colors = {
        "저비용·고인프라": "#2E8B57",
        "고비용·고인프라": "#E69F00",
        "저비용·저인프라": "#4C78A8",
        "고비용·저인프라": "#D9534F",
    }

    setup_font()

    fig, ax = plt.subplots(
        figsize=(13, 9),
    )

    # 영역별 산점도
    for category, color in colors.items():
        category_data = df[df["분류"] == category]

        ax.scatter(
            category_data["환산월세_2025_만원"],
            category_data["인프라종합점수"],
            color=color,
            label=category,
            s=100,
            alpha=0.85,
            edgecolor="white",
            linewidth=0.8,
        )

    # 월세 중앙값 기준선
    ax.axvline(
        rent_median,
        color="#555555",
        linestyle="--",
        linewidth=1.3,
    )

    # 인프라 중앙값 기준선
    ax.axhline(
        infrastructure_median,
        color="#555555",
        linestyle="--",
        linewidth=1.3,
    )

    # 자치구명 표시
    for _, row in df.iterrows():
        ax.annotate(
            row["자치구명"],
            (
                row["환산월세_2025_만원"],
                row["인프라종합점수"],
            ),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=9,
        )

    # 네 영역 이름 표시
    ax.text(
        0.02,
        0.97,
        "저비용·고인프라",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=colors["저비용·고인프라"],
    )

    ax.text(
        0.98,
        0.97,
        "고비용·고인프라",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=colors["고비용·고인프라"],
    )

    ax.text(
        0.02,
        0.03,
        "저비용·저인프라",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color=colors["저비용·저인프라"],
    )

    ax.text(
        0.98,
        0.03,
        "고비용·저인프라",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=12,
        fontweight="bold",
        color=colors["고비용·저인프라"],
    )

    # 상관분석 결과 표시
    correlation_text = (
        f"스피어맨 상관계수: {correlation:.4f}\n" f"p-value: {p_value:.4f}"
    )

    ax.text(
        0.02,
        0.86,
        correlation_text,
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "#999999",
            "alpha": 0.9,
        },
    )

    ax.set_title(
        "2025년 서울 자치구별 환산월세와 생활 인프라",
        fontsize=17,
        fontweight="bold",
        pad=18,
    )

    ax.set_xlabel(
        "2025년 환산월세 중앙값(만원)",
        fontsize=12,
    )

    ax.set_ylabel(
        "인프라 종합점수",
        fontsize=12,
    )

    ax.grid(
        alpha=0.2,
        linestyle=":",
    )

    ax.legend(
        loc="best",
        frameon=True,
    )

    fig.tight_layout()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    fig.savefig(
        OUTPUT_FILE,
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.close(fig)

    print(f"그래프 생성 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
