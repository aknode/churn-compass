import unittest
import pandas as pd
from fastapi.testclient import TestClient
from app.model import validate, score, OPTIONS, preprocess
from app.main import app
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression


def row():
    return {
        **{k: v[0] for k, v in OPTIONS.items()},
        "tenure": 10,
        "MonthlyCharges": 65,
        "TotalCharges": 650,
    }


class ModelTests(unittest.TestCase):
    def test_missing_feature_rejected(self):
        r = row()
        del r["Contract"]
        with self.assertRaises(ValueError):
            validate(pd.DataFrame([r]))

    def test_invalid_category_rejected(self):
        r = row()
        r["Contract"] = "unknown"
        with self.assertRaises(ValueError):
            validate(pd.DataFrame([r]))

    def test_negative_and_nonfinite_rejected(self):
        for v in [-1, float("inf"), "oops"]:
            r = row()
            r["MonthlyCharges"] = v
            with self.assertRaises(ValueError):
                validate(pd.DataFrame([r]))

    def test_blank_total_is_imputed(self):
        r = row()
        r["TotalCharges"] = " "
        self.assertTrue(pd.isna(validate(pd.DataFrame([r])).iloc[0].TotalCharges))

    def test_scoring_pipeline_and_threshold(self):
        rows = [
            {**row(), "tenure": i + 1, "TotalCharges": 65 * (i + 1)} for i in range(20)
        ]
        pipe = Pipeline([("pre", preprocess()), ("model", LogisticRegression())]).fit(
            pd.DataFrame(rows), [0] * 10 + [1] * 10
        )
        a = score(
            pd.DataFrame([rows[0], rows[-1]]), {"pipeline": pipe, "threshold": 0.5}
        )
        self.assertLess(a[0]["risk_score"], a[1]["risk_score"])
        self.assertFalse(a[0]["flagged"])
        self.assertTrue(a[1]["flagged"])

    def test_api_contract(self):
        c = TestClient(app)
        self.assertEqual(c.get("/health").status_code, 200)
        self.assertEqual(
            c.post("/api/predict", json={"customers": []}).status_code, 422
        )
        self.assertEqual(c.get("/api/cohort?limit=1000").status_code, 422)


if __name__ == "__main__":
    unittest.main()
