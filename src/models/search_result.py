from pydantic import BaseModel
from typing import List
from .chunk import ChunkMetadata


class SearchResult(BaseModel):
    """검색 결과 모델"""
    text: str
    score: float
    metadata: ChunkMetadata
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "검색된 텍스트 내용...",
                "score": 0.85,
                "metadata": {
                    "document_id": "uuid-here",
                    "chunk_index": 0,
                    "filename": "example.pdf",
                    "file_type": "pdf"
                }
            }
        }

