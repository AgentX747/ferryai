# ============================================================
# main.py — FastAPI app entry point
# Run: uvicorn app.main:app --reload --port 8000
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os


load_dotenv()

from app.routes import forecast, scenario
from app.core  import meta

app = FastAPI(
    title       = "Ferry Passenger Prediction API",
    description = "XGBoost v5 — Philippine ferry demand forecasting with oil price features",
    version     = "1.0.0",
    docs_url    = "/docs",    # Swagger UI  → http://localhost:8000/docs
    redoc_url   = "/redoc",   # ReDoc UI    → http://localhost:8000/redoc
)

# ── CORS — allow React (3000) and Express (5000) ─────────────
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ── Register routers ──────────────────────────────────────────
app.include_router(forecast.router)
app.include_router(scenario.router)

# ── Root endpoint ─────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status":       "online",
        "model":        f"ferry_xgboost_{meta['model_version']}",
        "accuracy":     f"{meta['accuracy_pct']}%",
        "pmos":         len(meta['pmo_list']),
        "docs":         "http://localhost:8000/docs",
    }

@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}

@app.get("/model-info", tags=["Health"])
def model_info():
    return {
        "model_version":   meta["model_version"],
        "accuracy_pct":    meta["accuracy_pct"],
        "mean_mape_pct":   meta["mean_mape_pct"],
        "features_count":  meta["features_count"],
        "training_rows":   meta["training_rows"],
        "avg_rounds":      meta["avg_rounds"],
        "training_years":  meta["training_years"],
        "forecast_months": meta["forecast_months"],
        "pmo_list":        meta["pmo_list"],
    }

@app.get("/pmos", tags=["Health"])
def get_pmos():
    return {
        "pmos":    meta["pmo_list"],
        "regions": meta["region_list"],
        "count":   len(meta["pmo_list"]),
    }
