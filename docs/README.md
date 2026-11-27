# Why-not 프로젝트 문서

이 폴더는 서울 청년 1인가구 분석 프로젝트의 데이터 출처와 전처리 기준을 기록합니다.

## 데이터 출처

- [데이터 출처](data_sources.md)

## 전처리 문서

| 분석 데이터 | 문서 |
|---|---|
| 청년 1인가구 | [청년 1인가구 전처리](preprocessing/youth_single_household.md) |
| 청년 인구 | [청년 인구 전처리](preprocessing/youth_population.md) |
| 전월세 | [전월세 전처리](preprocessing/rent_prices.md) |
| 생활물가 | [생활물가 전처리](preprocessing/living_prices.md) |
| 의료·편의시설 | [의료·편의시설 전처리](preprocessing/medical_retail_preprocessing_2025.md) |
| 버스·지하철 | [버스·지하철 전처리](preprocessing/subway_bus_preprocessing.md) |

## 문서 작성 기준

전처리 문서에는 데이터 출처와 원본 파일명, 분석 대상과 기준연도, 결측치·중복 처리 기준, 전처리 과정, 검증 결과, 출력 파일명과 실행 방법을 기록합니다.

## 데이터 관리

- 원본 데이터는 `data/raw/`에 보관합니다.
- 전처리 결과는 `data/processed/`에 보관합니다.
- `data/` 폴더의 파일은 GitHub에 업로드하지 않습니다.
- 원본 데이터는 직접 수정하지 않습니다.
- 데이터 기준이나 파일명을 변경하면 관련 문서도 함께 수정합니다.
- API 키와 비밀번호는 문서와 코드에 기록하지 않습니다.
