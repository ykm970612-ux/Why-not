from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_FILE = PROJECT_DIR / "data" / "raw" / "living_prices_2025_seoul.csv"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

TARGET_YEAR = 2025
MARKET_TYPE = "전통시장"
SEOUL_DISTRICT_COUNT = 25


def main():

    if not RAW_FILE.exists():
        raise FileNotFoundError(f"{RAW_FILE.name} 파일이 없습니다.")

    df = pd.read_csv(RAW_FILE, encoding="cp949", low_memory=False)

    columns = [
        "시장/마트 이름",
        "품목 번호",
        "품목 이름",
        "가격(원)",
        "년도-월",
        "시장유형 구분(시장/마트) 이름",
        "자치구 이름",
        "점검일자",
    ]

    df = df[columns].copy()
    df = df.drop_duplicates()

    # 문자열 앞뒤 공백 제거
    text_columns = [
        "시장/마트 이름",
        "품목 이름",
        "년도-월",
        "시장유형 구분(시장/마트) 이름",
        "자치구 이름",
    ]

    for column in text_columns:
        df[column] = df[column].astype("string").str.strip()

    # 숫자와 날짜 형식 정리
    df["품목 번호"] = pd.to_numeric(df["품목 번호"], errors="coerce")
    df["가격(원)"] = pd.to_numeric(df["가격(원)"], errors="coerce")
    df["점검일자"] = pd.to_datetime(df["점검일자"], errors="coerce")

    # 2025년 전통시장 자료 중 가격이 정상인 행만 사용
    df = df[
        (df["년도-월"].str[:4] == str(TARGET_YEAR))
        & (df["시장유형 구분(시장/마트) 이름"] == MARKET_TYPE)
        & (df["가격(원)"] > 0)
    ].copy()

    df = df.dropna(
        subset=["품목 번호", "품목 이름", "가격(원)", "자치구 이름", "점검일자"]
    )

    # 시장별 조사 횟수 차이의 영향을 줄이기 위해 자치구,월-품목별 중앙가격 계산
    district_item_month = df.groupby(
        ["자치구 이름", "년도-월", "품목 번호", "품목 이름"],
        as_index=False,
    ).agg(
        자치구_품목_중앙가격_원=("가격(원)", "median"),
        가격_관측건수=("가격(원)", "count"),
    )

    # 25개 자치구에 모두 존재하는 월-품목만 비교에 사용
    item_coverage = (
        district_item_month.groupby(
            ["년도-월", "품목 번호", "품목 이름"], as_index=False
        )["자치구 이름"]
        .nunique()
        .rename(columns={"자치구 이름": "자치구수"})
    )

    common_items = item_coverage[item_coverage["자치구수"] == SEOUL_DISTRICT_COUNT][
        ["년도-월", "품목 번호", "품목 이름"]
    ]

    district_item_month = district_item_month.merge(
        common_items,
        on=["년도-월", "품목 번호", "품목 이름"],
        how="inner",
    )

    # 같은 월-품목의 25개 자치구 중앙가격 중 중앙값을 서울 기준가격으로 사용
    seoul_item_month = (
        district_item_month.groupby(
            ["년도-월", "품목 번호", "품목 이름"], as_index=False
        )["자치구_품목_중앙가격_원"]
        .median()
        .rename(columns={"자치구_품목_중앙가격_원": "서울_품목_중앙가격_원"})
    )

    district_item_month = district_item_month.merge(
        seoul_item_month,
        on=["년도-월", "품목 번호", "품목 이름"],
        how="left",
    )

    # 서울 품목 중앙가격을 100으로 한 자치구별 품목 물가지수
    district_item_month["품목_물가지수"] = (
        district_item_month["자치구_품목_중앙가격_원"]
        / district_item_month["서울_품목_중앙가격_원"]
        * 100
    )

    # 자치구별 월간 생활물가지수
    monthly = (
        district_item_month.groupby(["자치구 이름", "년도-월"], as_index=False)
        .agg(
            생활물가지수=("품목_물가지수", "median"),
            비교품목수=("품목_물가지수", "count"),
        )
        .rename(columns={"자치구 이름": "자치구명"})
    )

    monthly["생활물가지수"] = monthly["생활물가지수"].round(2)

    # 12개월을 같은 비중으로 반영한 연간 생활물가지수
    yearly = (
        monthly.groupby("자치구명", as_index=False)
        .agg(
            생활물가지수=("생활물가지수", "mean"),
            분석월수=("년도-월", "nunique"),
            월평균_비교품목수=("비교품목수", "mean"),
        )
        .sort_values("자치구명")
        .reset_index(drop=True)
    )

    yearly.insert(1, "기준연도", TARGET_YEAR)
    yearly[["생활물가지수", "월평균_비교품목수"]] = yearly[
        ["생활물가지수", "월평균_비교품목수"]
    ].round(2)

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    monthly.to_csv(
        PROCESSED_DIR / "living_price_2025_monthly_district.csv",
        index=False,
        encoding="utf-8-sig",
    )

    yearly.to_csv(
        PROCESSED_DIR / "living_price_2025_district.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print("생활물가 데이터 전처리 완료")


if __name__ == "__main__":
    main()
