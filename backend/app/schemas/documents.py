from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DocumentPermissionSchema(BaseModel):
    id: str
    document_id: str
    allowed_role: str

    model_config = ConfigDict(from_attributes=True)


class DocumentResponse(BaseModel):
    id: str
    company_id: str
    title: str
    file_type: Optional[str] = None
    created_by: Optional[str] = None
    is_indexed: bool
    created_at: datetime
    allowed_roles: List[str] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentResponse
