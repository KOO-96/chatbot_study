from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """문서 메타데이터 모델"""
    filename: str
    file_type: str
    uploaded_at: Optional[datetime] = Field(default_factory=datetime.now)
    file_size: Optional[int] = None


class Document(BaseModel):
    """문서 모델"""
    document_id: str
    metadata: DocumentMetadata
    chunks_count: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "uuid-here",
                "metadata": {
                    "filename": "example.pdf",
                    "file_type": "pdf",
                    "uploaded_at": "2024-01-01T00:00:00",
                    "file_size": 1024
                },
                "chunks_count": 10
            }
        }

