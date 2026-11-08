import unittest

from src.preprocessing.healthnconv_preprocess_facilities import (
    DISTRICTS,
    count,
    medical,
    retail,
)


def medical_rows():
    return [
        {
            "암호화된요양기호": f"id-{i}",
            "요양기관명": f"의원-{i}",
            "요양종별": "의원",
            "시도명": "서울특별시",
            "시군구명": gu,
            "도로명주소": f"서울특별시 {gu} 도로 1",
            "표시과목명": "내과",
            "개설일자": "2024-01-01",
        }
        for i, gu in enumerate(DISTRICTS)
    ]


def retail_rows():
    return [
        {
            "기준_년분기_코드": "20254",
            "자치구_코드_명": gu,
            "서비스_업종_코드": code,
            "서비스_업종_코드_명": name,
            "전체_점포_수": "1,000.0",
            "일반_점포_수": "600",
            "프랜차이즈_점포_수": "400",
        }
        for gu in DISTRICTS
        for code, name in [("CS300001", "슈퍼마켓"), ("CS300002", "편의점")]
    ]


class FacilityTests(unittest.TestCase):
    def test_snapshot_includes_older_openings_and_retains_id_collisions(self):
        rows = medical_rows()
        rows[1]["암호화된요양기호"] = rows[0]["암호화된요양기호"]
        rows[1]["개설일자"] = "2025-12-31"
        result, audit = medical(rows + [rows[0].copy()])
        self.assertEqual(sum(r["일상의료시설수"] for r in result), 25)
        self.assertEqual(sum(r["종합의료시설수"] for r in result), 0)
        self.assertEqual(audit["exact_duplicates_removed"], 1)
        self.assertEqual(audit["rows_in_conflicting_id_groups"], 2)

    def test_medical_indicators_include_only_the_six_selected_types(self):
        rows = medical_rows()
        for kind in (
            "치과의원",
            "약국",
            "상급종합병원",
            "종합병원",
            "병원",
            "요양병원",
            "한의원",
            "조산원",
            "보건지소",
        ):
            rows.append(
                {**rows[0], "요양종별": kind, "암호화된요양기호": f"extra-{kind}"}
            )
        result, _ = medical(rows)
        self.assertEqual(
            result[0],
            {
                "자치구명": DISTRICTS[0],
                "기준연도": 2025,
                "기준월": 12,
                "기준일": 31,
                "일상의료시설수": 3,
                "종합의료시설수": 3,
            },
        )

    def test_medical_rejects_future_and_missing_district(self):
        rows = medical_rows()
        rows[0]["개설일자"] = "2026-01-01"
        with self.assertRaises(ValueError):
            medical(rows)
        with self.assertRaises(ValueError):
            medical(medical_rows()[1:])

    def test_retail_uses_only_2025_q4(self):
        rows = retail_rows()
        for period in ["20244", "20251", "20261"]:
            rows.append(
                {**rows[0], "기준_년분기_코드": period, "전체_점포_수": "99999"}
            )
        result, audit = retail(rows)
        self.assertEqual(audit["selected_rows"], 50)
        self.assertTrue(all(r["생활편의시설수"] == 2000 for r in result))

    def test_retail_rejects_duplicates_missing_categories_and_bad_totals(self):
        rows = retail_rows()
        for bad in [
            rows + [rows[0].copy()],
            rows[1:],
            [{**rows[0], "전체_점포_수": "999"}] + rows[1:],
        ]:
            with self.assertRaises(ValueError):
                retail(bad)

    def test_numeric_parsing_rejects_missing_negative_and_fractional_counts(self):
        self.assertEqual(count("1,234개"), 1234)
        for bad in ["", "-1", "1.5", "NaN", "Infinity"]:
            with self.assertRaises(ValueError):
                count(bad)


if __name__ == "__main__":
    unittest.main()
