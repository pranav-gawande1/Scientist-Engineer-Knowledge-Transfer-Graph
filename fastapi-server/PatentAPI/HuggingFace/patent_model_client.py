import os
from functools import lru_cache

from gradio_client import Client

SPACE_URL = os.getenv(
    "PATENT_MODEL_SPACE_URL",
    "https://Aryan-Ghadekar-patent-predictor.hf.space",
)

HF_TOKEN = os.getenv("HF_TOKEN")


@lru_cache
def get_client():
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN is not configured")

    return Client(
        "Aryan-Ghadekar/patent-predictor",
        headers={"Authorization": f"Bearer {HF_TOKEN}"},
    )


def predict_patent(
    title: str,
    abstract: str,
    keywords: str,
    year: int = 2005,
    cited: int = 0,
    novelty: float = 0.0,
    source: str = "unknown",
    past_patent_cnt: int = 0,
    avg_past_sim: float = 0.0,
    max_past_sim: float = 0.0,
):
    client = get_client()

    result = client.predict(
        title,
        abstract,
        keywords,
        year,
        cited,
        novelty,
        source,
        past_patent_cnt,
        avg_past_sim,
        max_past_sim,
        api_name="/predict",
    )

    return {
        "probability": result[0],
        "prediction": result[1],
        "confidence": result[2],
        "label": (
            "Likely to become a patent"
            if result[1] == 1
            else "Unlikely to become a patent"
        ),
        "top_drivers": result[3],
        "interpretation": result[4],
        "latency_ms": result[5],
    }
