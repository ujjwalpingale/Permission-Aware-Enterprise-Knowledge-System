from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's query question")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Question cannot be empty or contain only whitespace.")
        return v.strip()


class Citation(BaseModel):
    document_id: str = Field(..., description="Unique ID of the source document")
    title: str = Field(..., description="Human readable title of the source")
    source_type: str = Field(..., description="Type of source (project_document, support_ticket, slack)")


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer grounded in context")
    citations: List[Citation] = Field(default_factory=list, description="Source citations used for answer")


class HealthResponse(BaseModel):
    status: str = "ok"
