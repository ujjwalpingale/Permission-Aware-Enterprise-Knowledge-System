from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    user_id: Optional[str] = Field(None, description="Legacy user ID (optional; ignored for authorization in favor of JWT token)")
    question: str = Field(..., description="The user's query question")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str) and not v.strip():
            return None
        return v.strip()

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
