from functools import lru_cache
import io, json
import pandas as pd
import joblib
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from app.model import BASE, FEATURES, OPTIONS, score

app = FastAPI(title="Churn Compass", version="1.0.0")
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


@app.get("/")
def home():
    return FileResponse(BASE / "static/index.html")


@app.get("/health")
def health():
    return {"status": "ok", "model_ready": (BASE / "artifacts/model.joblib").exists()}


@lru_cache(maxsize=1)
def bundle():
    path = BASE / "artifacts/model.joblib"
    if not path.exists():
        raise HTTPException(503, "Run python -m app.bootstrap first.")
    return joblib.load(path)


@app.get("/api/summary")
def summary():
    path = BASE / "artifacts/metrics.json"
    if not path.exists():
        raise HTTPException(503, "Run python -m app.bootstrap first.")
    return json.loads(path.read_text())


@app.get("/api/schema")
def schema():
    return {"features": FEATURES, "options": OPTIONS}


@app.get("/api/cohort")
def cohort(limit: int = 20):
    if not 1 <= limit <= 500:
        raise HTTPException(422, "limit must be 1 to 500")
    path = BASE / "artifacts/holdout_scores.csv"
    if not path.exists():
        raise HTTPException(503, "Run bootstrap first.")
    x = pd.read_csv(path)
    return json.loads(
        x[
            [
                "customerID",
                "tenure",
                "Contract",
                "MonthlyCharges",
                "risk_score",
                "actual_churn",
            ]
        ]
        .head(limit)
        .to_json(orient="records")
    )


class Batch(BaseModel):
    customers: list[dict] = Field(min_length=1, max_length=10000)


@app.post("/api/predict")
def predict(payload: Batch):
    try:
        return {"predictions": score(pd.DataFrame(payload.customers), bundle())}
    except ValueError as e:
        raise HTTPException(422, str(e))


@app.post("/api/predict-csv")
async def predict_csv(request: Request):
    body = await request.body()
    if len(body) > 5_000_000:
        raise HTTPException(413, "CSV must be under 5 MB.")
    try:
        x = pd.read_csv(io.BytesIO(body))
        pred = score(x, bundle())
        out = pd.DataFrame(pred)
        if "customerID" in x:
            out.insert(
                0,
                "customerID",
                x.customerID.astype(str).str.replace(r"^[=+@-]", "_", regex=True),
            )
        return Response(
            out.to_csv(index=False),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=churn_predictions.csv"
            },
        )
    except (ValueError, UnicodeError, pd.errors.ParserError) as e:
        raise HTTPException(422, str(e))


@app.get("/api/sample-csv")
def sample():
    return FileResponse(
        BASE / "examples/customers.csv", media_type="text/csv", filename="customers.csv"
    )
