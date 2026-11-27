import unittest

import pandas as pd

from src.calculate_final_scores import INDICATOR_COLUMNS, calculate_scores


class CalculateFinalScoresTest(unittest.TestCase):
    def test_five_domains_receive_equal_weight(self):
        first = {column: 0.0 for column in INDICATOR_COLUMNS}
        first.update(
            {
                "자치구명": "가구",
                "청년1인가구_LQ_2025_정규화": 1.0,
            }
        )

        second = {column: 0.3 for column in INDICATOR_COLUMNS}
        second["자치구명"] = "나구"

        result = calculate_scores(pd.DataFrame([first, second])).set_index("자치구명")

        self.assertAlmostEqual(result.loc["가구", "청년집중도점수"], 1.0)
        self.assertAlmostEqual(result.loc["가구", "종합점수"], 0.2)
        self.assertAlmostEqual(result.loc["나구", "종합점수"], 0.3)
        self.assertEqual(result.loc["나구", "종합순위"], 1)
        self.assertEqual(result.loc["가구", "종합순위"], 2)

    def test_normalized_values_must_be_between_zero_and_one(self):
        row = {column: 0.5 for column in INDICATOR_COLUMNS}
        row.update(
            {
                "자치구명": "가구",
                "청년1인가구_LQ_2025_정규화": 1.1,
            }
        )

        with self.assertRaisesRegex(ValueError, "0 이상 1 이하"):
            calculate_scores(pd.DataFrame([row]))


if __name__ == "__main__":
    unittest.main()
