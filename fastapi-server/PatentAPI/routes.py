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

from fastapi import FastAPI, HTTPException, Request, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from .service import _run_inference
from .models import PaperInput, PredictionResponse, TextOnlyInput, BatchInput, BatchResponse

patent_router = APIRouter(prefix="/api/model_predict", tags=["Model"])

# ── Logging ─────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("patent_api")

# ── Artefact paths (override via env vars for Docker / cloud deploy) ─────────
MODEL_PATH  = os.getenv("MODEL_PATH",  "outputs/patent_predictor_v4.pkl")
SCALER_PATH = os.getenv("SCALER_PATH", "outputs/patent_scaler_v4.pkl")
TFIDF_PATH  = os.getenv("TFIDF_PATH",  "outputs/patent_tfidf_v4.pkl")
SVD_PATH    = os.getenv("SVD_PATH",    "outputs/patent_svd_v4.pkl")
META_PATH   = os.getenv("META_PATH",   "outputs/patent_meta_v4.pkl")

# ── Global artefact store ────────────────────────────────────────────────────
ARTS: dict = {}

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
# MIDDLEWARE — request timing
# ══════════════════════════════════════════════════════════════
# @patent_router.middleware("http")
# async def add_latency_header(request: Request, call_next):
#     start = time.perf_counter()
#     response = await call_next(request)
#     ms = (time.perf_counter() - start) * 1000
#     response.headers["X-Latency-Ms"] = f"{ms:.1f}"
#     return response


# ══════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════

@patent_router.get("/health", tags=["System"])
def health():
    """Liveness check — returns model version and cutoff year."""
    meta = ARTS.get("meta", {})
    return {
        "status":      "ok",
        "model":       "patent_predictor_v4",
        "cutoff_year": meta.get("cutoff_year"),
        # "threshold":   meta.get("threshold"),
        "artefacts_loaded": len(ARTS) == 5,
    }


@patent_router.get("/model/info", tags=["System"])
def model_info():
    """Full model metadata: features, thresholds, and test-set metrics."""
    meta = ARTS.get("meta", {})
    return {
        "struct_features": meta.get("struct_features", []),
        "svd_components":  meta.get("svd_components"),
        "top_sim_threshold": meta.get("top_sim"),
        "bot_sim_threshold": meta.get("bot_sim"),
        # "decision_threshold": meta.get("threshold"),
        "cutoff_year":     meta.get("cutoff_year"),
        "test_metrics":    meta.get("test_metrics", {}),
    }
# @patent_router.post("/predict", response_model=PredictionResponse, tags=["Prediction"])
# def predict(paper: PaperInput):
#     """
#     Full prediction — accepts all structured metadata alongside text.

#     Provide as much of title, abstract, and keywords as possible for
#     best accuracy. Structured fields (year, cited, novelty, etc.) are
#     optional but improve predictions when available.
#     """
#     if not paper.title and not paper.abstract and not paper.keywords:
#         raise HTTPException(
#             status_code=422,
#             detail="Provide at least one of: title, abstract, keywords."
#         )
#     t0     = time.perf_counter()
#     result = _run_inference(paper)
#     result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
#     log.info(
#         f"/predict  prob={result['probability']:.3f}  "
#         f"conf={result['confidence']}  {result['latency_ms']}ms"
#     )
#     return result

from .HuggingFace.patent_model_client import predict_patent


@patent_router.post(
    "/predict",
    response_model=PredictionResponse,
    tags=["Prediction"],
)
def predict(paper: PaperInput):

    try:
        result = predict_patent(
            title=paper.title,
            abstract=paper.abstract,
            keywords=paper.keywords,
            year=paper.year,
            cited=paper.cited,
            novelty=paper.novelty,
            source=paper.source,
            past_patent_cnt=paper.past_patent_cnt,
            avg_past_sim=paper.avg_past_sim,
            max_past_sim=paper.max_past_sim,
        )

        return result

    except Exception as exc:
        log.exception("Patent model request failed")

        raise HTTPException(
            status_code=502,
            detail="Patent prediction service is unavailable.",
        ) from exc


@patent_router.post("/predict/text", response_model=PredictionResponse, tags=["Prediction"])
def predict_text(inp: TextOnlyInput):
    """
    Text-only prediction — supply just title, abstract, and keywords.

    All structured metadata (year, citations, novelty, etc.) default to zero.
    Ideal for quickly screening papers when only the text is available.
    """
    paper = PaperInput(
        title=inp.title,
        abstract=inp.abstract,
        keywords=inp.keywords,
    )
    t0     = time.perf_counter()
    result = _run_inference(paper)
    result["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)
    log.info(
        f"/predict/text  prob={result['probability']:.3f}  "
        f"conf={result['confidence']}  {result['latency_ms']}ms"
    )
    return result


@patent_router.post("/predict/batch", response_model=BatchResponse, tags=["Prediction"])
def predict_batch(batch: BatchInput):
    """
    Batch prediction — submit up to 100 papers in a single request.

    Each paper uses the same full schema as /predict.
    Results are returned in the same order as the input list.
    """
    t0      = time.perf_counter()
    results = []
    for paper in batch.papers:
        t1     = time.perf_counter()
        result = _run_inference(paper)
        result["latency_ms"] = round((time.perf_counter() - t1) * 1000, 2)
        results.append(result)

    total_ms = round((time.perf_counter() - t0) * 1000, 2)
    log.info(f"/predict/batch  n={len(results)}  total={total_ms}ms")
    return {"count": len(results), "results": results, "total_ms": total_ms}


# ══════════════════════════════════════════════════════════════
# GLOBAL ERROR HANDLER
# ══════════════════════════════════════════════════════════════
# @patent_router.exception_handler(Exception)
# async def generic_error_handler(request: Request, exc: Exception):
#     log.error(f"Unhandled error on {request.url}: {exc}", exc_info=True)
#     return JSONResponse(
#         status_code=500,
#         content={"detail": "Internal server error. Check server logs."},
#     )