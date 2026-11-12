from pathlib import Path
import json
import re
import pandas as pd

# 1. 파일 경로
PROJECT_DIR = Path(__file__).resolve().parents[2]
SUBWAY_FILE = PROJECT_DIR / "data" / "raw" / 'subway_stations_2025_seoulmetro.csv'
BOUNDARY_FILE = PROJECT_DIR / "data" / "raw" / 'seoul.geojson.json'
OUTPUT_DIR = PROJECT_DIR / "data" / "processed" / '서울시_지하철_전처리결과'


def minmax(series):
    # 최댓값과 최솟값이 같으면 0으로 처리
    minimum, maximum = series.min(), series.max()
    if maximum == minimum:
        return pd.Series(0.0, index=series.index)

    normalized = (series - minimum) / (maximum - minimum)
    return normalized.round(4)


def main():
    # 2. 원본 데이터 읽기 및 검증
    df = pd.read_csv(SUBWAY_FILE, encoding='cp949', dtype=str)
    with BOUNDARY_FILE.open(encoding='utf-8') as f:
        geo = json.load(f)
    boundary = pd.DataFrame(
        [
            {
                '자치구코드': str(feature['properties']['code']),
                '자치구명': feature['properties']['name'],
            }
            for feature in geo['features']
        ]
    )
    if len(boundary) != 25 or boundary['자치구명'].duplicated().any():
        raise ValueError('자치구 경계가 25개인지 확인하세요.')
    required = {'역번호', '호선', '역명', '도로명주소'}
    if not required.issubset(df.columns):
        raise ValueError(f'지하철 파일 누락 컬럼: {sorted(required - set(df.columns))}')

    # 3. 주소에서 서울시 자치구 추출 및 경계 목록과 대조
    for col in required:
        df[col] = df[col].astype('string').str.strip()
    df['자치구명'] = df['도로명주소'].str.extract(
        r'^(?:서울특별시|서울시)\s*([가-힣]+구)', expand=False
    )
    code_by_gu = boundary.set_index('자치구명')['자치구코드']
    df['자치구코드'] = df['자치구명'].map(code_by_gu)
    valid = df[df['자치구코드'].notna()].copy()
    unmatched = df[df['자치구코드'].isna()].copy()

    # 4. 같은 자치구의 동일 역명은 환승 중복으로 보고 1개 역으로 집계
    valid['역명_정리'] = valid['역명'].str.replace(
        r'\s+', '', regex=True
    )
    physical = valid.groupby(['자치구코드', '자치구명', '역명_정리'], as_index=False).agg(
        역명=('역명', 'first'),
        노선수=('호선', 'nunique'),
        노선목록=(
            '호선', lambda s: ', '.join(sorted(s.dropna().unique()))
        ),
        원자료행수=('역번호', 'size'),
    )
    physical['환승역여부'] = (
        physical['노선수'].gt(1).map({True: '예', False: '아니오'})
    )

    # 5. 자치구별 물리적 역 수 집계 및 Min-Max 정규화
    counts = physical.groupby('자치구코드').size().rename('물리적_역수')
    summary = boundary.merge(counts, on='자치구코드', how='left')
    summary['물리적_역수'] = summary['물리적_역수'].fillna(0).astype(int)
    summary['물리적_역수_minmax'] = minmax(summary['물리적_역수'])
    summary = summary.sort_values('자치구코드').reset_index(drop=True)

    # 6. 결과 저장
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    summary.to_csv(
        OUTPUT_DIR / '자치구별_지하철역_집계.csv',
        index=False,
        encoding='utf-8-sig',
    )
    with pd.ExcelWriter(OUTPUT_DIR / '지하철역_자치구별_전처리결과.xlsx') as writer:
        summary.to_excel(writer, sheet_name='자치구별_집계_정규화', index=False)
        physical.to_excel(writer, sheet_name='환승중복제거_역목록', index=False)
        valid.to_excel(writer, sheet_name='노선별_자치구분류', index=False)
        unmatched.to_excel(writer, sheet_name='자치구_미분류', index=False)
    print(
        f'완료: 원본 {len(df)}행 / 분류 {len(valid)}행 / '
        f'미분류 {len(unmatched)}행 / 물리적 역 {len(physical)}개'
    )
    print(f'저장 위치: {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
