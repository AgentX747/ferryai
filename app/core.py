# ============================================================
# core.py — loads all model files ONCE at startup
# All routes import from here — no repeated file loading
# ============================================================

import joblib, json, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

MODEL_DIR = Path(os.getenv("MODEL_DIR", "./model_files"))

def _load(filename):
    path = MODEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing model file: {path}\n"
            f"Make sure you copied all .pkl and .json files to {MODEL_DIR}"
        )
    return path

# ── Load everything once ──────────────────────────────────────
print(f"Loading model files from: {MODEL_DIR.resolve()}")

model     = joblib.load(_load("ferry_model.pkl"))
le_pmo    = joblib.load(_load("le_pmo.pkl"))
le_region = joblib.load(_load("le_region.pkl"))
FEATURES  = joblib.load(_load("features_list.pkl"))

with open(_load("fuel_lookup.json"))         as f: fuel_lookup  = json.load(f)
with open(_load("oil_lookup.json"))          as f: oil_lookup   = json.load(f)
with open(_load("pmo_history.json"))         as f: pmo_history  = json.load(f)
with open(_load("model_meta.json"))          as f: meta         = json.load(f)
with open(_load("national_forecast.json"))   as f: nat_forecast = json.load(f)
with open(_load("national_historical.json")) as f: nat_hist     = json.load(f)

print(f"  ✅ Model loaded  ({meta['avg_rounds']} trees, {meta['features_count']} features)")
print(f"  ✅ {len(meta['pmo_list'])} PMOs ready")
print(f"  ✅ Accuracy: {meta['accuracy_pct']}%")

# ── Feature lists (must match training order) ─────────────────
FUEL_FEATURES = [
    'Price_Diesel_USD','Price_Premium_Gasoline_USD','Price_Regular_Gasoline_USD',
    'Fuel_Diesel_MoM','Fuel_Diesel_Lag1','Fuel_Diesel_Lag3',
    'Fuel_Diesel_Roll3','Fuel_Diesel_Spike','Fuel_Diesel_YoY','Global_Avg_Diesel_USD',
]
OIL_FEATURES = ['Brent_vs_trend','Brent_YoY','Oil_Shock_Flag']

MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
             'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}
MONTH_INV = {v:k for k,v in MONTH_MAP.items()}

# ── Lookup helpers ────────────────────────────────────────────
def get_fuel(year: int, month_str: str) -> dict:
    key     = f"{year}_{month_str}"
    default = list(fuel_lookup.values())[-1]
    return fuel_lookup.get(key, default)

def get_oil(year: int, month_str: str) -> dict:
    key     = f"{year}_{month_str}"
    default = list(oil_lookup.values())[-1]
    return oil_lookup.get(key, default)
