"""
응답 스키마 정의

모든 API 응답 DTO를 한 파일로 관리합니다.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from src.models.search_result import SearchResult
from src.models.document import Document


class UploadResponse(BaseModel):
    """파일 업로드 응답 DTO"""
    message: str = Field(..., description="응답 메시지")
    filename: str = Field(..., description="업로드된 파일명")
    chunks_count: int = Field(..., description="생성된 청크 개수")
    document_id: str = Field(..., description="문서 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "파일 업로드 및 벡터화 완료",
                "filename": "example.pdf",
                "chunks_count": 15,
                "document_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class QueryResponse(BaseModel):
    """질의 응답 DTO"""
    query: str = Field(..., description="사용자 질문")
    answer: str = Field(..., description="생성된 답변")
    contexts: List[str] = Field(..., description="관련 문서 컨텍스트 리스트")
    sources: List[SearchResult] = Field(..., description="검색 결과 소스")
    top_k: int = Field(..., description="사용된 top_k 값")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "문서의 주요 내용은 무엇인가요?",
                "answer": "질문: 문서의 주요 내용은 무엇인가요?\n\n관련 문서에서 찾은 정보:\n\n...",
                "contexts": ["관련 텍스트 청크 1", "관련 텍스트 청크 2"],
                "sources": [
                    {
                        "text": "관련 텍스트...",
                        "score": 0.85,
                        "metadata": {
                            "document_id": "uuid-here",
                            "chunk_index": 0,
                            "filename": "example.pdf",
                            "file_type": "pdf"
                        }
                    }
                ],
                "top_k": 5
            }
        }


class DocumentListResponse(BaseModel):
    """문서 목록 응답 DTO"""
    documents: List[Document] = Field(..., description="저장된 문서 목록")
    total_count: int = Field(..., description="전체 문서 개수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "document_id": "uuid-here",
                        "metadata": {
                            "filename": "example.pdf",
                            "file_type": "pdf",
                            "uploaded_at": "2024-01-01T00:00:00",
                            "file_size": 1024
                        },
                        "chunks_count": 10
                    }
                ],
                "total_count": 1
            }
        }


class DocumentDeleteResponse(BaseModel):
    """문서 삭제 응답 DTO"""
    message: str = Field(..., description="응답 메시지")
    document_id: str = Field(..., description="삭제된 문서 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "문서가 성공적으로 삭제되었습니다.",
                "document_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class BaseResponse(BaseModel):
    """기본 응답 스키마"""
    message: Optional[str] = Field(None, description="응답 메시지")
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    error: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Validation Error",
                "detail": "필수 필드가 누락되었습니다."
            }
        }


class DocumentDebugInfo(BaseModel):
    """문서 디버깅 정보"""
    document_id: str = Field(..., description="문서 ID")
    filename: str = Field(..., description="파일명")
    chunks_found: int = Field(..., description="찾은 청크 수")
    avg_score: float = Field(..., description="평균 점수")
    max_score: float = Field(..., description="최대 점수")
    min_score: float = Field(..., description="최소 점수")


class DebugQueryResponse(QueryResponse):
    """디버깅 정보가 포함된 질의 응답 DTO"""
    debug_info: dict = Field(..., description="디버깅 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "문서의 주요 내용은 무엇인가요?",
                "answer": "질문: 문서의 주요 내용은 무엇인가요?\n\n관련 문서에서 찾은 정보:\n\n...",
                "contexts": ["관련 텍스트 청크 1", "관련 텍스트 청크 2"],
                "sources": [],
                "top_k": 5,
                "debug_info": {
                    "searched_documents": [
                        {
                            "document_id": "uuid-here",
                            "filename": "example.pdf",
                            "chunks_found": 3,
                            "avg_score": 0.85,
                            "max_score": 0.92,
                            "min_score": 0.78
                        }
                    ],
                    "total_documents_found": 1
                }
            }
        }

