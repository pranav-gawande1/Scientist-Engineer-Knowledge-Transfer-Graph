import os
import re
import time
import logging
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Optional

import numpy as np
import pandas as pd
import joblib

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from .models import PaperInput

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("patent_api")

# ── Artefact paths (override via env vars for Docker / cloud deploy) ─────────
# MODEL_PATH  = os.getenv("MODEL_PATH",  "outputs/patent_predictor_v4.pkl")
# SCALER_PATH = os.getenv("SCALER_PATH", "outputs/patent_scaler_v4.pkl")
# TFIDF_PATH  = os.getenv("TFIDF_PATH",  "outputs/patent_tfidf_v4.pkl")
# SVD_PATH    = os.getenv("SVD_PATH",    "outputs/patent_svd_v4.pkl")
# META_PATH   = os.getenv("META_PATH",   "outputs/patent_meta_v4.pkl")

# ── Global artefact store ────────────────────────────────────────────────────
# ARTS: dict = {}

# ══════════════════════════════════════════════════════════════
# STARTUP / SHUTDOWN
# ══════════════════════════════════════════════════════════════
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model artefacts once at startup; release on shutdown."""
    log.info("Loading model artefacts ...")
    for path in [MODEL_PATH, SCALER_PATH, TFIDF_PATH, SVD_PATH, META_PATH]:
        if not os.path.exists(path):
            raise RuntimeError(
                f"Artefact not found: {path}\n"
                "Run  python patent_predictor_v4.py  first to train and save the model."
            )
    ARTS["model"]  = joblib.load(MODEL_PATH)
    ARTS["scaler"] = joblib.load(SCALER_PATH)
    ARTS["tfidf"]  = joblib.load(TFIDF_PATH)
    ARTS["svd"]    = joblib.load(SVD_PATH)
    ARTS["meta"]   = joblib.load(META_PATH)
    ARTS["meta"]["threshold"] = 0.6
    log.info("✓ Model artefacts loaded successfully.")
    yield
    ARTS.clear()
    log.info("Artefacts released.")
# ══════════════════════════════════════════════════════════════
# CORE INFERENCE LOGIC
# ══════════════════════════════════════════════════════════════
# def clean_text(t: str) -> str:
#     t = str(t).lower()
#     t = re.sub(r"[^a-z0-9\s]", " ", t)
#     t = re.sub(r"\s+", " ", t).strip()
#     return t

# def _run_inference(paper: PaperInput) -> dict:
#     """Build feature vector and return prediction dict (robust to missing fields)."""

#     meta   = ARTS.get("meta")
#     model  = ARTS["model"]
#     scaler = ARTS["scaler"]
#     tfidf  = ARTS["tfidf"]
#     svd    = ARTS["svd"]

#     threshold    = meta["threshold"]
#     cutoff       = meta["cutoff_year"]
#     bot_sim      = meta.get("bot_sim", 0.34)
#     le           = meta["label_encoder"]
#     struct_feats = meta["struct_features"]

#     # ─────────────────────────────────────────
#     # ✅ SAFE INPUT HANDLING (CRITICAL FIX)
#     # ─────────────────────────────────────────
#     title    = getattr(paper, "title", "")
#     abstract = getattr(paper, "abstract", "") or ""
#     keywords = getattr(paper, "keywords", "") or ""

#     year    = getattr(paper, "year", 2000) or 2000
#     cited   = getattr(paper, "cited", 0) or 0
#     novelty = getattr(paper, "novelty", 0.0) or 0.0
#     source  = getattr(paper, "source", "unknown") or "unknown"

#     past_patent_cnt = getattr(paper, "past_patent_cnt", 0) or 0
#     avg_past_sim    = getattr(paper, "avg_past_sim", 0.0) or 0.0
#     max_past_sim    = getattr(paper, "max_past_sim", 0.0) or 0.0

#     # ─────────────────────────────────────────
#     # STRUCT FEATURES
#     # ─────────────────────────────────────────
#     age = max(cutoff - year, 0)

#     if le is not None:
#         try:
#             domain_enc = int(le.transform([source])[0])
#         except:
#             domain_enc = 0
#     else:
#         domain_enc = 0

#     kws = [k.strip() for k in keywords.split(",") if k.strip()]

#     struct_row = {
#         "novelty": novelty,
#         "novelty_bin": float(int(pd.cut(
#             [novelty],
#             bins=[-np.inf, 0, 0.25, 0.5, 0.75, np.inf],
#             labels=[0, 1, 2, 3, 4]
#         )[0])),

#         "domain_encoded": domain_enc,
#         "age_at_cutoff": age,
#         "is_recent": int(age <= 5),

#         "cited_log": np.log1p(cited),
#         "cited_log_rate": np.log1p(cited / max(age, 1)),

#         "past_patent_log": np.log1p(past_patent_cnt),
#         "avg_past_sim": avg_past_sim,
#         "max_past_sim": max_past_sim,
#         "has_past_patent": int(max_past_sim >= bot_sim),

#         "keyword_count": len(kws),
#         "keyword_diversity": len(set(k.lower() for k in kws)),
#         "abstract_words": len(abstract.split()),
#     }

#     X_struct = np.array([[struct_row.get(f, 0) for f in struct_feats]])

#     # ─────────────────────────────────────────
#     # TEXT FEATURES
#     # ─────────────────────────────────────────
#     blob = clean_text(f"{title} {abstract} {keywords}")

#     X_tfidf = tfidf.transform([blob])
#     X_text  = svd.transform(X_tfidf)

#     # ─────────────────────────────────────────
#     # COMBINE
#     # ─────────────────────────────────────────
#     X = scaler.transform(np.hstack([X_struct, X_text]))

#     # ─────────────────────────────────────────
#     # PREDICTION
#     # ─────────────────────────────────────────
#     prob = float(model.predict_proba(X)[0, 1])
#     pred = int(prob > threshold)

#     # ─────────────────────────────────────────
#     # CONFIDENCE
#     # ─────────────────────────────────────────
#     if prob >= 0.75:
#         confidence = "High"
#     elif prob >= 0.50:
#         confidence = "Medium"
#     elif prob >= 0.30:
#         confidence = "Low-Medium"
#     else:
#         confidence = "Low"

#     # ─────────────────────────────────────────
#     # FEATURE IMPORTANCE
#     # ─────────────────────────────────────────
#     base_model  = model.calibrated_classifiers_[0].estimator
#     importances = base_model.feature_importances_[:len(struct_feats)]
#     top_idx     = np.argsort(importances)[::-1][:3]
#     top_drivers = [struct_feats[i] for i in top_idx]

#     # ─────────────────────────────────────────
#     # INTERPRETATION
#     # ─────────────────────────────────────────
#     if prob >= 0.70:
#         interp = f"Strong signal ({prob:.0%}) — high patent potential."
#     elif prob >= 0.45:
#         interp = f"Moderate signal ({prob:.0%}) — can be improved."
#     else:
#         interp = f"Weak signal ({prob:.0%}) — low patent likelihood."

#     return {
#         "probability": round(prob, 4),
#         "prediction": pred,
#         "confidence": confidence,
#         "label": "Likely to become a patent" if pred else "Unlikely to become a patent",
#         "top_drivers": top_drivers,
#         "interpretation": interp,
#     }