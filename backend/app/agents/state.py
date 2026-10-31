import operator
from typing import Annotated, Any, TypedDict


class PipelineState(TypedDict, total=False):
    # inputs
    resume_text: str
    jd_text: str
    company: str
    role: str
    weeks: int
    session_id: str
    # outputs
    parsed_resume: dict
    ats: dict
    skills: dict          # {matched, missing, weak, extra}
    context: dict         # {company_kb, jd_snippets}
    interview_questions: list[dict]
    coding_questions: list[dict]
    roadmap: dict
    generation_mode: str  # groq | offline
    warnings: Annotated[list[str], operator.add]
    trace: Annotated[list[str], operator.add]
    _internal: Any
