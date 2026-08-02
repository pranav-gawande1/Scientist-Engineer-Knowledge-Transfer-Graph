import logging
import time

from fastapi import APIRouter, HTTPException

from PatentAPI.HuggingFace.patent_model_client import predict_patent

from .service import (
    save_and_link_paper,
    get_matches,
    generate_roadmap,
    store_in_postgres,
)

from .schemas import PipelineInput

# ── force logging config here too, in case it's not inherited ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("patent_api")


roadmap_router = APIRouter(
    prefix="/api/pipeline",
    tags=["Roadmap"],
)


@roadmap_router.post("/analyze")
def analyze_pipeline(paper: dict):

    log.info(f"[/analyze] Incoming request: {paper}")

    paper_obj = PipelineInput(**paper)
    log.info(f"[/analyze] Parsed PipelineInput OK")

    try:
        log.info("[/analyze] Calling predict_patent...")
        t0 = time.perf_counter()

        prediction = predict_patent(
            title=paper_obj.title,
            abstract=paper_obj.abstract,
            keywords=paper_obj.keywords,
            year=paper_obj.year,
            cited=paper_obj.cited,
            novelty=paper_obj.novelty,
            source=paper_obj.source,
            past_patent_cnt=paper_obj.past_patent_cnt,
            avg_past_sim=paper_obj.avg_past_sim,
            max_past_sim=paper_obj.max_past_sim,
        )

        log.info(f"[/analyze] predict_patent succeeded in {time.perf_counter()-t0:.2f}s: {prediction}")

    except Exception as exc:
        log.error(f"[/analyze] predict_patent FAILED: {type(exc).__name__}: {exc}")
        log.exception("[/analyze] Full traceback:")

        raise HTTPException(
            status_code=502,
            detail="Patent prediction service is unavailable.",
        ) from exc

    store_in_postgres(paper_obj, prediction)
    save_and_link_paper(paper, prediction)
    roadmap = generate_roadmap(paper_obj)

    return {
        "paper": paper_obj.model_dump(),
        "prediction": prediction,
        "roadmap": roadmap,
    }