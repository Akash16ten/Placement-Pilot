from typing import Optional

from pydantic import BaseModel, Field


class InterviewStartRequest(BaseModel):
    session_id: str
    num_questions: int = Field(5, ge=3, le=10)


class InterviewAnswerRequest(BaseModel):
    answer: str = Field(..., min_length=1, max_length=4000)


class TaskUpdate(BaseModel):
    task_id: str
    done: bool


class CodingLog(BaseModel):
    title: str
    topics: list[str] = []
    rating: str = Field(..., pattern="^(easy|ok|hard|failed)$")  # how it felt
    minutes: Optional[int] = Field(None, ge=0, le=600)


class ScoreIn(BaseModel):
    kind: str = Field(..., pattern="^(mock_test|self_assessment)$")
    ref: str = ""
    score: float = Field(..., ge=0, le=100)
