from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

PROJECT_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_DIR / "data" / "processed" / "weight_sensitivity_random.csv"

OUTPUT_FILE = PROJECT_DIR / "outputs" / "charts" / "weight_sensitivity_frequency.png"

REQUIRED_COLUMNS = [
    "자치구명",
    "상위3위_포함비율",
    "상위5위_포함비율",
]


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


def create_chart(df):
    chart_data = (
        df.sort_values("상위5위_포함비율", ascending=False)
        .head(10)
        .sort_values("상위5위_포함비율")
    )

    y = np.arange(len(chart_data))
    height = 0.35

    fig, ax = plt.subplots(figsize=(10, 7))

    ax.barh(
        y - height / 2,
        chart_data["상위3위_포함비율"],
        height=height,
        label="상위 3위 포함 비율",
        color="#377D58",
    )

    ax.barh(
        y + height / 2,
        chart_data["상위5위_포함비율"],
        height=height,
        label="상위 5위 포함 비율",
        color="#9BC4A8",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(chart_data["자치구명"])
    ax.set_xlim(0, 100)
    ax.set_xlabel("포함 비율(%)")
    ax.set_title("무작위 가중치 20,000회 적용 시 상위권 포함 비율")
    ax.legend()
    ax.grid(axis="x", alpha=0.2)

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


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE.name} 파일이 없습니다. "
            "가중치 민감도 분석 코드를 먼저 실행하세요."
        )

    df = pd.read_csv(
        INPUT_FILE,
        encoding="utf-8-sig",
    )

    setup_font()
    create_chart(df)

    print(f"그래프 생성 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
