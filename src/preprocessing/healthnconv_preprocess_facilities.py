"""서울 25개 자치구의 2025년 의료·생활편의시설 집계 (Python 표준 라이브러리)."""

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import quantiles

ROOT = Path(__file__).resolve().parents[2]
DISTRICTS = tuple(
    sorted(
        "종로구 중구 용산구 성동구 광진구 동대문구 중랑구 성북구 강북구 도봉구 노원구 은평구 서대문구 마포구 양천구 강서구 구로구 금천구 영등포구 동작구 관악구 서초구 강남구 송파구 강동구".split()
    )
)
MEDICAL_TYPES = (
    "상급종합병원",
    "종합병원",
    "병원",
    "의원",
    "치과병원",
    "치과의원",
    "한방병원",
    "한의원",
    "요양병원",
    "정신병원",
    "보건소",
    "보건지소",
    "보건진료소",
    "보건의료원",
    "조산원",
    "약국",
)
MEDICAL_INDICATORS = {
    "일상의료시설수": ("의원", "치과의원", "약국"),
    "종합의료시설수": ("상급종합병원", "종합병원", "병원"),
}
RETAIL_TYPES = {"CS300001": "슈퍼마켓", "CS300002": "편의점"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(path):
    content = Path(path).read_bytes()
    for encoding in ("utf-8-sig", "cp949"):
        try:
            text = content.decode(encoding)
            break
        except UnicodeDecodeError:
            continue
    else:
        raise ValueError(f"지원하지 않는 인코딩: {path}")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    rows = list(reader)
    require(bool(rows), f"빈 파일: {path}")
    require(
        all(None not in row and None not in row.values() for row in rows),
        f"CSV 열 수 오류: {path}",
    )
    return (
        rows,
        {
            "filename": Path(path).name,
            "encoding": encoding,
            "rows": len(rows),
            "sha256": hashlib.sha256(content).hexdigest(),
        },
        text,
    )


def require_columns(rows, names):
    require(
        set(names) <= rows[0].keys(), f"필수 컬럼 누락: {set(names) - rows[0].keys()}"
    )


def district(value):
    result = re.sub(r"\s+", "", value).removeprefix("서울특별시").removeprefix("서울시")
    require(result in DISTRICTS, f"서울 자치구명 오류: {value!r}")
    return result


def count(value):
    cleaned = re.sub(r"[,\s]", "", value)
    cleaned = re.sub(r"(개|원|%)$", "", cleaned)
    try:
        number = Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"숫자 변환 실패: {value!r}") from exc
    require(
        number.is_finite() and number >= 0 and number == number.to_integral_value(),
        f"음수/비정수/결측 점포 수: {value!r}",
    )
    return int(number)


def missing_counts(rows):
    return {key: sum(not row[key].strip() for row in rows) for key in rows[0]}


def medical(rows):
    keys = (
        "암호화된요양기호",
        "요양기관명",
        "요양종별",
        "시도명",
        "시군구명",
        "도로명주소",
        "표시과목명",
        "개설일자",
    )
    require_columns(rows, keys)
    seoul = [r for r in rows if r["시도명"].strip() == "서울특별시"]
    require(bool(seoul), "서울 의료기관 없음")
    missing = missing_counts(seoul)
    for key in keys:
        if key != "표시과목명":
            require(missing[key] == 0, f"의료 필수값 결측: {key}")
    # 원본 식별자 충돌이 있으므로 전체 필드가 동일한 행만 중복 제거한다.
    unique = {tuple(r[k].strip() for k in keys): r for r in seoul}
    selected = list(unique.values())
    ids = Counter(r["암호화된요양기호"].strip() for r in selected)
    natural_keys = Counter(
        tuple(r[k].strip() for k in keys if k != "암호화된요양기호") for r in selected
    )
    require(
        max(natural_keys.values()) == 1,
        "내용이 같고 식별자만 다른 의료기관: 수동 검토 필요",
    )
    grouped = defaultdict(Counter)
    early_dates = 0
    for row in selected:
        gu = district(row["시군구명"])
        kind = row["요양종별"].strip()
        require(kind in MEDICAL_TYPES, f"알 수 없는 요양종별: {kind}")
        opened = date.fromisoformat(row["개설일자"].strip())
        require(
            opened <= date(2025, 12, 31),
            "2025년 이후 개설 의료기관 발견: 기준일 확인 필요",
        )
        early_dates += opened < date(1950, 1, 1)
        grouped[gu][kind] += 1
    require(set(grouped) == set(DISTRICTS), "의료 자치구 누락")
    output = []
    for gu in DISTRICTS:
        row = {"자치구명": gu, "기준연도": 2025, "기준월": 12, "기준일": 31}
        for indicator, kinds in MEDICAL_INDICATORS.items():
            row[indicator] = sum(grouped[gu][kind] for kind in kinds)
        output.append(row)
    return output, {
        "seoul_rows": len(seoul),
        "missing_values": missing,
        "exact_duplicates_removed": len(seoul) - len(selected),
        "conflicting_id_groups": sum(n > 1 for n in ids.values()),
        "rows_in_conflicting_id_groups": sum(n for n in ids.values() if n > 1),
        "opening_dates_before_1950_retained": early_dates,
        "opening_date_min": min(r["개설일자"] for r in selected),
        "opening_date_max": max(r["개설일자"] for r in selected),
        "validated_snapshot_rows": len(selected),
        "indicator_totals": {
            key: sum(r[key] for r in output) for key in MEDICAL_INDICATORS
        },
    }


def retail(rows):
    keys = (
        "기준_년분기_코드",
        "자치구_코드_명",
        "서비스_업종_코드",
        "서비스_업종_코드_명",
        "전체_점포_수",
        "일반_점포_수",
        "프랜차이즈_점포_수",
    )
    require_columns(rows, keys)
    selected = [
        r
        for r in rows
        if r["기준_년분기_코드"].strip() == "20254"
        and r["서비스_업종_코드"].strip() in RETAIL_TYPES
    ]
    require(bool(selected), "2025년 4분기 편의점/슈퍼마켓 없음")
    missing = missing_counts(selected)
    require(all(missing[k] == 0 for k in keys), "상권 필수값 결측")
    grouped = defaultdict(dict)
    for row in selected:
        gu = district(row["자치구_코드_명"])
        code = row["서비스_업종_코드"].strip()
        require(code not in grouped[gu], f"상권 자치구·업종 중복: {gu}, {code}")
        require(
            row["서비스_업종_코드_명"].strip() == RETAIL_TYPES[code],
            "상권 업종 코드/이름 불일치",
        )
        total, general, franchise = (
            count(row[k])
            for k in ("전체_점포_수", "일반_점포_수", "프랜차이즈_점포_수")
        )
        require(total == general + franchise, f"점포 수 합계 불일치: {gu}, {code}")
        grouped[gu][code] = total
    require(set(grouped) == set(DISTRICTS), "상권 자치구 누락")
    output = []
    for gu in DISTRICTS:
        require(set(grouped[gu]) == set(RETAIL_TYPES), f"상권 업종 누락: {gu}")
        output.append(
            {
                "자치구명": gu,
                "기준연도": 2025,
                "기준분기": 4,
                "편의점수": grouped[gu]["CS300002"],
                "슈퍼마켓수": grouped[gu]["CS300001"],
                "생활편의시설수": sum(grouped[gu].values()),
            }
        )
    return output, {
        "input_period_counts": dict(
            sorted(Counter(r["기준_년분기_코드"] for r in rows).items())
        ),
        "selected_period": 20254,
        "selected_rows": len(selected),
        "missing_values": missing,
        "total_stores": sum(r["생활편의시설수"] for r in output),
    }


def outliers(rows, columns):
    result = {}
    for key in columns:
        q1, _, q3 = quantiles([r[key] for r in rows], n=4, method="inclusive")
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        result[key] = {
            "lower_fence": low,
            "upper_fence": high,
            "flagged": [
                {"자치구명": r["자치구명"], "value": r[key]}
                for r in rows
                if not low <= r[key] <= high
            ],
        }
    return result


def write_csv(path, rows):
    require(
        len(rows) == 25 and {r["자치구명"] for r in rows} == set(DISTRICTS),
        "출력 자치구 검증 실패",
    )
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--medical-input",
        type=Path,
        default=ROOT / "data/raw/medical_facilities_2025_hira.csv",
    )
    parser.add_argument(
        "--retail-input",
        type=Path,
        default=ROOT / "data/raw/retail_stores_2025_seoul.csv",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    args = parser.parse_args()
    med_rows, med_source, _ = read_csv(args.medical_input)
    retail_rows, retail_source, _ = read_csv(args.retail_input)
    med, med_audit = medical(med_rows)
    stores, retail_audit = retail(retail_rows)
    # 모든 검증을 통과한 뒤에만 결과를 작성한다.
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "medical_facilities_clean_2025.csv", med)
    write_csv(args.output_dir / "retail_stores_clean_2025.csv", stores)
    audit = {
        "year": 2025,
        "district_count": 25,
        "normalization": "사용자 요청으로 인구·면적 보정 제외",
        "medical": {"source": med_source, **med_audit},
        "retail": {"source": retail_source, **retail_audit},
        "outliers_retained": {
            "medical": outliers(med, MEDICAL_INDICATORS),
            "retail": outliers(stores, ["편의점수", "슈퍼마켓수", "생활편의시설수"]),
        },
    }
    (args.output_dir / "facilities_validation_2025.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8-sig"
    )
    totals = med_audit["indicator_totals"]
    print(
        f"완료: 의료 {len(med)}개 구 / 일상의료 {totals['일상의료시설수']:,}개 / "
        f"종합의료 {totals['종합의료시설수']:,}개, 생활편의 {len(stores)}개 구 / {retail_audit['total_stores']:,}개"
    )


if __name__ == "__main__":
    main()
