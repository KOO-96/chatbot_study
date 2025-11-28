from typing import Optional
from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """청크 메타데이터 모델"""
    document_id: str
    chunk_index: int
    filename: Optional[str] = None
    file_type: Optional[str] = None


class Chunk(BaseModel):
    """텍스트 청크 모델"""
    text: str
    metadata: ChunkMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "청크 텍스트 내용...",
                "metadata": {
                    "document_id": "uuid-here",
                    "chunk_index": 0,
                    "filename": "example.pdf",
                    "file_type": "pdf"
                }
            }
        }

