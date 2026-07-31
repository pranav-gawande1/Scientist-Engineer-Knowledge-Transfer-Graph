"""
paper_review.py  —  Research Paper Quality Review + Plagiarism Detection Route
================================================================================
Paste this file into your project and add to main.py:

    from paper_review import router as paper_review_router
    app.include_router(paper_review_router)

Requirements (add to requirements.txt):
    fastapi
    python-multipart
    openai>=1.0.0
    pymupdf
    pillow
    python-dotenv   # optional
"""

import re
import json
import io
import os
import json
import base64
from PIL import Image
import fitz  # PyMuPDF

# importing ai client
from services.ai_service import AIClient

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
# from openai import OpenAI

# ── Router ─────────────────────────────────────────────────────────────────────
router = APIRouter(prefix="/paper-review", tags=["Paper Review"])


# ── OpenAI client ──────────────────────────────────────────────────────────────
def get_ai_client():
    return AIClient()


# ══════════════════════════════════════════════════════════════════════════════
#  PROMPTS
# ══════════════════════════════════════════════════════════════════════════════

# ── Peer-Review System Prompt ──────────────────────────────────────────────────
REVIEW_SYSTEM_PROMPT = """You are a strict, experienced senior academic peer reviewer with 15+ years of 
experience reviewing papers for top-tier venues (NeurIPS, ICML, ACL, IEEE, Nature, Science, ACM).

Your job is to evaluate research papers with the same rigor as a top conference program committee.
Be critical, precise, and evidence-based. Do NOT be lenient or overly encouraging.

Evaluate the paper on these 8 dimensions, scoring each from 1–10:
1. Novelty & Originality     — Is the contribution genuinely new?
2. Technical Soundness       — Are methods, proofs, and experiments rigorous?
3. Clarity & Writing Quality — Is the paper well-structured and clearly written?
4. Experimental Rigor        — Fair baselines, ablations, statistical significance?
5. Related Work Coverage     — Is prior work cited thoroughly and accurately?
6. Reproducibility           — Enough detail to reproduce results?
7. Significance & Impact     — Will this matter to the field?
8. Ethical Considerations    — Are limitations, biases, and societal impacts acknowledged?

Return ONLY valid JSON (no markdown fences, no extra keys):

{
  "overall_verdict": "STRONG ACCEPT | ACCEPT | WEAK ACCEPT | BORDERLINE | WEAK REJECT | REJECT | STRONG REJECT",
  "confidence": "HIGH | MEDIUM | LOW",
  "overall_score": <1-10 float>,
  "scores": {
    "novelty": <1-10>,
    "technical_soundness": <1-10>,
    "clarity": <1-10>,
    "experimental_rigor": <1-10>,
    "related_work": <1-10>,
    "reproducibility": <1-10>,
    "significance": <1-10>,
    "ethics": <1-10>
  },
  "strengths": ["<point>", ...],
  "weaknesses": ["<point>", ...],
  "major_concerns": ["<critical issue>", ...],
  "minor_concerns": ["<minor issue>", ...],
  "questions_for_authors": ["<question>", ...],
  "summary": "<2-3 sentence summary>",
  "detailed_review": "<full peer review narrative, minimum 300 words>",
  "recommendation_rationale": "<precise explanation of accept/reject decision>"
}"""

REVIEW_USER_TEMPLATE = """Please perform a rigorous peer review of the following research paper.

--- PAPER TEXT START ---
{text}
--- PAPER TEXT END ---

{image_note}

Apply the strictest academic standards. If the paper has fatal flaws, say so clearly.
Respond ONLY with valid JSON matching the schema in the system prompt."""


# ── Plagiarism Detection System Prompt ────────────────────────────────────────
PLAGIARISM_SYSTEM_PROMPT = """You are an expert academic integrity analyst specializing in detecting 
plagiarism, text reuse, and academic misconduct in research papers.

IMPORTANT DISCLAIMER: You do NOT have access to external databases (Turnitin, CrossRef, etc.).
Your analysis is based purely on linguistic and structural signals within the provided text.
This is an AI-based heuristic analysis, NOT a certified plagiarism report.

Analyze the paper for these plagiarism signals:

1. STYLE INCONSISTENCY — Sudden shifts in vocabulary complexity, sentence structure, or tone
   that suggest text was copied from different sources.

2. CITATION ANOMALIES — Claims made without citations, references cited but not discussed,
   mismatched citation styles, or suspicious clustering of citations.

3. INTERNAL DUPLICATION — Paragraphs, sentences, or phrases repeated verbatim or near-verbatim
   within the paper itself (self-plagiarism / patch-writing).

4. BOILERPLATE LANGUAGE — Generic, textbook-style definitions or introductions that read
   like they were lifted directly from Wikipedia or standard textbooks.

5. UNNATURAL TRANSITIONS — Abrupt topic jumps or sections that do not logically connect,
   suggesting patchwork assembly from multiple sources.

6. VOICE INCONSISTENCY — Sudden changes in writing persona (e.g., first-person to passive,
   formal to informal, British to American spelling within sections).

7. OVER-SPECIFIC DETAILS WITHOUT CONTEXT — Highly specific statistics, equations, or claims
   that appear without explanation, suggesting they were copied without understanding.

8. SUSPICIOUS PARAPHRASING — Sentences that appear to be mechanical paraphrases of
   well-known passages (changing only nouns/verbs while keeping structure identical).

For each signal found, quote the suspicious text excerpt.

Estimate plagiarism percentage using this scale:
  0–10%   : Likely original — minor boilerplate only
  11–25%  : Low concern — some paraphrasing or reused phrases detected
  26–40%  : Moderate concern — multiple style shifts and reused passages
  41–60%  : High concern — significant sections appear non-original
  61–80%  : Very high concern — majority of content shows reuse signals
  81–100% : Severe — paper appears to be largely copied/assembled from other works

Return ONLY valid JSON (no markdown fences):

{
  "plagiarism_likelihood": "VERY LOW | LOW | MODERATE | HIGH | VERY HIGH | SEVERE",
  "estimated_plagiarism_percentage": <0-100 integer>,
  "confidence": "HIGH | MEDIUM | LOW",
  "disclaimer": "This is an AI heuristic analysis based on linguistic signals only. It does not replace certified plagiarism detection tools like iThenticate or Turnitin.",
  "overall_assessment": "<2-3 sentence summary of plagiarism risk>",
  "signals_found": [
    {
      "type": "STYLE_INCONSISTENCY | CITATION_ANOMALY | INTERNAL_DUPLICATION | BOILERPLATE | UNNATURAL_TRANSITION | VOICE_INCONSISTENCY | OVER_SPECIFIC_DETAIL | SUSPICIOUS_PARAPHRASE",
      "severity": "LOW | MEDIUM | HIGH",
      "location": "<page/section reference if identifiable>",
      "excerpt": "<suspicious text snippet, max 100 words>",
      "explanation": "<why this is flagged>"
    }
  ],
  "clean_sections": ["<sections that appear original>"],
  "high_risk_sections": ["<sections with highest reuse signals>"],
  "recommendations": ["<action 1>", "<action 2>", ...]
}"""

PLAGIARISM_USER_TEMPLATE = """Analyze the following research paper text for plagiarism signals.
Be thorough and flag every suspicious pattern you detect. Do not be lenient.

--- PAPER TEXT START ---
{text}
--- PAPER TEXT END ---

Respond ONLY with valid JSON matching the schema in the system prompt."""

# ══════════════════════════════════════════════════════════════════════════════
# Technical Review
# ══════════════════════════════════════════════════════════════════════════════
TECHNICAL_REVIEW_SYSTEM_PROMPT = """
You are a senior academic reviewer with over 20 years of experience reviewing research papers for IEEE, ACM, Springer, Elsevier, NeurIPS, ICML, ACL, CVPR, and Nature conferences and journals.

Your task is NOT to summarize the paper.

Your task is to perform a rigorous technical review and generate actionable reviewer comments exactly as a conference reviewer would.

Instructions:

1. Critically evaluate the paper based only on the provided content.
2. Do not invent missing information.
3. Do not praise the paper unnecessarily.
4. Only report issues that are actually supported by evidence in the manuscript.
5. Every observation must be specific and technically justified.
6. Avoid generic comments such as "Improve methodology" unless you explain WHY.
7. Focus on improvements that would increase the probability of publication.
8. If a particular aspect is strong, do not mention it in the weaknesses.
9. If an issue cannot be determined from the paper, state that it could not be assessed.
10. Write comments in formal reviewer language suitable for an IEEE or ACM conference.

Evaluate the paper across the following aspects:

• Novelty and Originality
• Problem Statement
• Research Objectives
• Literature Review
• Methodology
• Technical Soundness
• Experimental Design
• Dataset Quality
• Baselines and Comparative Analysis
• Statistical Validation
• Result Interpretation
• Discussion
• Reproducibility
• Figures and Tables
• Writing Quality
• Organization
• References
• Limitations
• Practical Impact

Return ONLY valid JSON.

{
  "review_comments":[
    {
      "id":1,
      "category":"Novelty",
      "severity":"Critical | Major | Minor",
      "comment":"Reviewer comment",
      "recommendation":"Specific improvement"
    }
  ]
}
"""
TECHNICAL_REVIEW_USER_PROMPT = """
Review the following research paper as an expert conference reviewer.

Identify ONLY the weaknesses, deficiencies, missing components, unsupported claims, methodological issues, experimental limitations, writing problems, and publication risks.

Do NOT generate positive feedback.

Generate between 8 and 15 reviewer comments depending on the quality of the manuscript.

Each comment should:

• Identify one issue.
• Explain why it is a problem.
• Suggest a concrete improvement.
• Be technically detailed.
• Be suitable for inclusion in an official conference review.

--- PAPER TEXT START ---
{text}
--- PAPER TEXT END ---
"""

# ══════════════════════════════════════════════════════════════════════════════
#  PDF EXTRACTION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

MAX_CHARS = 25000  # ~6000-7000 tokens

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract full text from all pages using PyMuPDF."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages_text.append(f"[Page {i + 1}]\n{text}")
    doc.close()
    full_text = "\n\n".join(pages_text)
    # Truncate to ~120k chars to stay within GPT-4o context limits
    if len(full_text) > MAX_CHARS:
        full_text = full_text[:MAX_CHARS] + "\n\n[... truncated for token limits ...]"
    return full_text


def extract_images_from_pdf(pdf_bytes: bytes, max_images: int = 8) -> list[dict]:
    """
    Extract embedded raster images from the PDF.
    Skips images smaller than 5KB (decorative/icons).
    Returns list of {page, index, base64, mime}.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    extracted = []
    for page_num, page in enumerate(doc):
        if len(extracted) >= max_images:
            break
        for img_index, img in enumerate(page.get_images(full=True)):
            if len(extracted) >= max_images:
                break
            xref = img[0]
            try:
                base_image = doc.extract_image(xref)
                img_bytes = base_image["image"]
                if len(img_bytes) < 5_000:
                    continue  # skip tiny decorative images
                pil_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                if pil_img.width > 1024 or pil_img.height > 1024:
                    pil_img.thumbnail((1024, 1024), Image.LANCZOS)
                buf = io.BytesIO()
                pil_img.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                extracted.append(
                    {
                        "page": page_num + 1,
                        "index": img_index,
                        "base64": b64,
                        "mime": "image/png",
                    }
                )
            except Exception:
                continue
    doc.close()
    return extracted


def render_pages_as_images(pdf_bytes: bytes, max_pages: int = 2) -> list[dict]:
    """
    Rasterize first N pages at ~108 DPI for visual layout analysis.
    Returns list of {page, base64, mime}.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    rendered = []
    for page_num in range(min(max_pages, len(doc))):
        page = doc[page_num]
        mat = fitz.Matrix(1.5, 1.5)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        b64 = base64.b64encode(pix.tobytes("png")).decode("utf-8")
        rendered.append({"page": page_num + 1, "base64": b64, "mime": "image/png"})
    doc.close()
    return rendered


def get_pdf_metadata(pdf_bytes: bytes) -> dict:
    """Extract basic PDF metadata."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    meta = doc.metadata or {}
    page_count = len(doc)
    word_count = sum(len(page.get_text("text").split()) for page in doc)
    doc.close()
    return {
        "page_count": page_count,
        "word_count": word_count,
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "subject": meta.get("subject", ""),
        "creator": meta.get("creator", ""),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  GPT CALL HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def build_vision_content(prompt_text: str, images: list[dict]) -> list:
    """Build content array with text + images for GPT-4o vision."""
    content = [{"type": "text", "text": prompt_text}]
    for img in images[:12]:  # GPT-4o supports up to ~20 images
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['mime']};base64,{img['base64']}",
                    "detail": "low",  # switch to "high" for richer analysis
                },
            }
        )
    return content


def call_gpt(client, system, content, max_tokens=3000):

    response = client.chat_completion(
        system=system,
        content=content,
        max_tokens=max_tokens,
        temperature=0.2,
    )

    raw = response.choices[0].message.content.strip()


    # Remove any markdown code fences
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        parsed = {"raw_response": raw, "parse_error": str(e)}

    usage = {
        "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
        "completion_tokens": getattr(response.usage, "completion_tokens", 0),
        "total_tokens": getattr(response.usage, "total_tokens", 0),
    }

    return parsed, usage


# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/review",
    summary="Full paper analysis: peer review + plagiarism detection",
    description=(
        "Upload a research paper PDF to get:\n"
        "- **Peer review** with scores across 8 academic dimensions\n"
        "- **Accept/Reject verdict** with rationale\n"
        "- **Plagiarism analysis** with estimated percentage and flagged sections\n"
        "- **Extracted figures** analyzed visually by GPT-4o"
    ),
)
async def review_paper(
    file: UploadFile = File(..., description="Research paper PDF"),
    include_images: bool = Form(
        True, description="Extract and analyze embedded figures"
    ),
    render_first_pages: bool = Form(
        True, description="Rasterize first 2 pages for visual analysis"
    ),
    run_plagiarism_check: bool = Form(
        True, description="Run plagiarism signal detection"
    ),
):
    # ── Validate ─────────────────────────────────────────────────────────
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(pdf_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB.")

    # ── Extract content ──────────────────────────────────────────────────
    try:
        text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF text extraction failed: {e}")

    if len(text.strip()) < 200:
        raise HTTPException(
            status_code=422,
            detail="Could not extract readable text. The PDF may be scanned/image-only.",
        )

    metadata = get_pdf_metadata(pdf_bytes)

    extracted_images: list[dict] = []
    rendered_pages: list[dict] = []

    if include_images:
        try:
            extracted_images = extract_images_from_pdf(pdf_bytes, max_images=8)
        except Exception:
            pass

    if render_first_pages:
        try:
            rendered_pages = render_pages_as_images(pdf_bytes, max_pages=2)
        except Exception:
            pass

    all_images = rendered_pages + extracted_images

    # ── Build prompts ────────────────────────────────────────────────────
    image_note = (
        f"I have also provided {len(all_images)} image(s) from the paper "
        "(rendered pages and/or extracted figures). Factor them into your review."
        if all_images
        else ""
    )

    review_prompt = REVIEW_USER_TEMPLATE.format(text=text, image_note=image_note)
    plagiarism_prompt = PLAGIARISM_USER_TEMPLATE.format(text=text)

    # ── Call GPT ─────────────────────────────────────────────────────────
    client = get_ai_client()
    total_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    # 1. Peer review (with images)
    try:
        review_content = review_prompt
        review_data, review_usage = call_gpt(
            client, REVIEW_SYSTEM_PROMPT, review_content, max_tokens=3000
        )
        for k in total_usage:
            total_usage[k] += review_usage[k]
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Peer review API call failed: {e}")

    # 2. Plagiarism check (text-only — no images needed)
    plagiarism_data = None
    if run_plagiarism_check:
        try:
            plag_content = plagiarism_prompt
            plagiarism_data, plag_usage = call_gpt(
                client, PLAGIARISM_SYSTEM_PROMPT, plag_content, max_tokens=2500
            )
            for k in total_usage:
                total_usage[k] += plag_usage[k]
        except Exception as e:
            plagiarism_data = {"error": f"Plagiarism check failed: {e}"}

    # ── Compose response ─────────────────────────────────────────────────
    return JSONResponse(
        content={
            "status": "success",
            "file": {
                "name": file.filename,
                "pages": metadata["page_count"],
                "word_count": metadata["word_count"],
                "title": metadata.get("title") or "N/A",
                "author": metadata.get("author") or "N/A",
                "images_extracted": len(extracted_images),
                "pages_rendered": len(rendered_pages),
            },
            "tokens_used": total_usage,
            "peer_review": review_data,
            "plagiarism_analysis": plagiarism_data,
        }
    )


# ── Peer review only ───────────────────────────────────────────────────────────
@router.post(
    "/review-only",
    summary="Peer review only (no plagiarism check)",
    description="Cheaper endpoint — runs only the peer review, skips plagiarism detection.",
)
async def review_only(
    file: UploadFile = File(...),
    include_images: bool = Form(True),
    render_first_pages: bool = Form(True),
):
    return await review_paper(
        file=file,
        include_images=include_images,
        render_first_pages=render_first_pages,
        run_plagiarism_check=False,
    )


# ── Plagiarism check only ─────────────────────────────────────────────────────
@router.post(
    "/plagiarism-only",
    summary="Plagiarism detection only (no peer review)",
    description="Cheaper endpoint — runs only plagiarism signal analysis.",
)
async def plagiarism_only(
    file: UploadFile = File(..., description="Research paper PDF"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF text extraction failed: {e}")

    if len(text.strip()) < 200:
        raise HTTPException(status_code=422, detail="Could not extract readable text.")

    metadata = get_pdf_metadata(pdf_bytes)
    plagiarism_prompt = PLAGIARISM_USER_TEMPLATE.format(text=text)
    client = get_ai_client()
    try:
        plag_content = plagiarism_prompt
        plagiarism_data, usage = call_gpt(
            client, PLAGIARISM_SYSTEM_PROMPT, plag_content, max_tokens=2500
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")

    return JSONResponse(
        content={
            "status": "success",
            "file": {
                "name": file.filename,
                "pages": metadata["page_count"],
                "word_count": metadata["word_count"],
            },
            "tokens_used": usage,
            "plagiarism_analysis": plagiarism_data,
        }
    )


# techinical review
@router.post(
    "/technical-review",
    summary="Technical Review",
    description="Give technical review of paper rather than of grammar and plagarism",
)
async def plagiarism_only(
    file: UploadFile = File(..., description="Research paper PDF"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        text = extract_text_from_pdf(pdf_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF text extraction failed: {e}")

    if len(text.strip()) < 200:
        raise HTTPException(status_code=422, detail="Could not extract readable text.")

    metadata = get_pdf_metadata(pdf_bytes)
    plagiarism_prompt = TECHNICAL_REVIEW_USER_PROMPT.format(text=text)
    client = get_ai_client()
    try:
        plag_content = plagiarism_prompt
        technical_review_data, usage = call_gpt(
            client, TECHNICAL_REVIEW_SYSTEM_PROMPT, plag_content, max_tokens=2500
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e}")

    return JSONResponse(
        content={
            "status": "success",
            "file": {
                "name": file.filename,
                "pages": metadata["page_count"],
                "word_count": metadata["word_count"],
            },
            "tokens_used": usage,
            "technical_review": technical_review_data,
        }
    )



# ── Health ─────────────────────────────────────────────────────────────────────
@router.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok", "module": "paper_review"}
