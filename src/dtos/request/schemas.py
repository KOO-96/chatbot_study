"""
요청 스키마 정의

모든 API 요청 DTO를 한 파일로 관리합니다.
"""
from pydantic import BaseModel, Field, field_validator


class QueryRequest(BaseModel):
    """질의 요청 DTO"""
    query: str = Field(..., description="검색할 질문", min_length=1)
    top_k: int = Field(default=5, description="반환할 관련 문서 개수", ge=1, le=20)
    
    @field_validator("query")
    @classmethod
    def validate_query_not_empty(cls, v: str) -> str:
        """질문이 공백만 있는지 검증"""
        if not v or not v.strip():
            raise ValueError("질문이 제공되지 않았습니다.")
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "문서의 주요 내용은 무엇인가요?",
                "top_k": 5
            }
        }


class DocumentDeleteRequest(BaseModel):
    """문서 삭제 요청 DTO"""
    document_id: str = Field(..., description="삭제할 문서 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }

