from pydantic import BaseModel

class PipelineInput(BaseModel):
    title: str
    abstract: str
    year: int
    cited: int
    novelty: float
    source: str
    keywords: str = ""
    past_patent_cnt: int = 0
    avg_past_sim: float = 0.0
    max_past_sim: float = 0.0