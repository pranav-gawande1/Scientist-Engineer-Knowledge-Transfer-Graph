import os
import time
from functools import lru_cache

from gradio_client import Client

SPACE_URL = os.getenv(
    "PATENT_MODEL_SPACE_URL",
    "https://Aryan-Ghadekar-patent-predictor.hf.space",
)

HF_TOKEN = os.getenv("HF_TOKEN",)  # removed hardcoded fallback - rotate your token!


import logging
log = logging.getLogger("patent_api")

@lru_cache
def get_client():
    log.info(f"[get_client] HF_TOKEN present: {bool(HF_TOKEN)}")
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not configured")

    log.info("[get_client] Creating gradio_client.Client...")
    c = Client(
        "Aryan-Ghadekar/patent-predictor",
        token=HF_TOKEN,
    )
    log.info("[get_client] Client created successfully")
    return c

def predict_patent(title, abstract, keywords, year=2005, cited=0, novelty=0.0,
                    source="unknown", past_patent_cnt=0, avg_past_sim=0.0,
                    max_past_sim=0.0, max_retries=4, retry_delay=10):
    client = get_client()
    last_exc = None

    for attempt in range(max_retries):
        log.info(f"[predict_patent] Attempt {attempt + 1}/{max_retries}")
        try:
            result = client.predict(
                title, abstract, keywords, year, cited, novelty,
                source, past_patent_cnt, avg_past_sim, max_past_sim,
                api_name="/predict",
            )
            log.info(f"[predict_patent] Raw result from HF: {result}")
            return {
                "probability": result[0],
                "prediction": result[1],
                "confidence": result[2],
                "label": "Likely to become a patent" if result[1] == 1 else "Unlikely to become a patent",
                "top_drivers": result[3],
                "interpretation": result[4],
                "latency_ms": result[5],
            }
        except Exception as exc:
            log.error(f"[predict_patent] Attempt {attempt + 1} failed: {type(exc).__name__}: {exc}")
            last_exc = exc
            if attempt < max_retries - 1:
                log.info(f"[predict_patent] Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

    log.error("[predict_patent] All retries exhausted")
    raise last_exc