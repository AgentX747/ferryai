# ============================================================
# Pydantic schemas — request and response shapes
# ============================================================

from pydantic import BaseModel, Field
from typing import Optional, List

# ── Requests ─────────────────────────────────────────────────

class PMOForecastRequest(BaseModel):
    pmo: str = Field(..., example="PMO Batangas")
    n_months: Optional[int] = Field(24, ge=1, le=48)

class ScenarioRequest(BaseModel):
    scenario: str = Field(..., example="mild")
    # baseline pulled from model_meta.json automatically

# ── Response items ────────────────────────────────────────────

class MonthlyForecast(BaseModel):
    year:       int
    month:      str
    month_num:  int
    date:       str
    predicted:  int
    lower:      int
    upper:      int
    oil_shock:  bool = False

class HistoricalMonth(BaseModel):
    year:      int
    month:     str
    month_num: int
    date:      str
    total:     int

class FoldResult(BaseModel):
    fold:     int
    mape:     float
    accuracy: float

class ScenarioResult(BaseModel):
    scenario:          str
    oil_change_pct:    float
    demand_change_pct: float
    baseline_M:        float
    adjusted_M:        float
    diesel_usd:        float
    diesel_php:        float

# ── Full responses ────────────────────────────────────────────

class ModelInfoResponse(BaseModel):
    model_version:   str
    accuracy_pct:    float
    mean_mape_pct:   float
    features_count:  int
    training_rows:   int
    avg_rounds:      int
    training_years:  str
    forecast_months: int

class PMOForecastResponse(BaseModel):
    pmo:      str
    forecast: List[MonthlyForecast]
    meta:     dict

class NationalResponse(BaseModel):
    historical: List[HistoricalMonth]
    forecast:   List[MonthlyForecast]
    accuracy:   str
