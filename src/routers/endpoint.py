from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging

from src.dtos.response import UploadResponse, DocumentListResponse, DocumentDeleteResponse, DebugQueryResponse
from src.dtos.request import QueryRequest
from src.dtos.response import QueryResponse
from src.services.document_service import DocumentService
from src.services.rag_service import RAGService
from src.dependencies import get_document_service, get_rag_service
from src.utils import (
    handle_router_error,
    handle_file_upload_error
)

logger = logging.getLogger(__name__)


def create_document_router() -> APIRouter:
    """문서 관리 라우터 생성"""
    router = APIRouter(prefix="/api/v1/document", tags=["document"])
    
    @router.post("", response_model=UploadResponse)
    async def upload_document(
        file: UploadFile = File(...),
        document_service: DocumentService = Depends(get_document_service)
    ):
        """
        PDF 또는 TXT 파일 업로드 및 벡터화
        
        - **file**: 업로드할 파일 (PDF 또는 TXT)
        """
        try:
            # 서비스를 통한 파일 업로드 처리 (파일 저장, 검증, 벡터화, 정리 포함)
            document = await document_service.upload_file_from_request(file)
            
            return UploadResponse(
                message="파일 업로드 및 벡터화 완료",
                filename=document.metadata.filename,
                chunks_count=document.chunks_count,
                document_id=document.document_id
            )
        
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise handle_file_upload_error(e, None, None)
    
    @router.get("/info", response_model=DocumentListResponse)
    async def get_documents_info(
        document_service: DocumentService = Depends(get_document_service)
    ):
        """저장된 문서 목록 조회 (문서 확인용)"""
        try:
            documents = await document_service.list_all_documents()
            return DocumentListResponse(
                documents=documents,
                total_count=len(documents)
            )
        except Exception as e:
            raise handle_router_error(e, "Document list retrieval", 500, "문서 목록 조회 중 오류가 발생했습니다.")
    
    @router.delete("/{document_id}", response_model=DocumentDeleteResponse)
    async def delete_document(
        document_id: str,
        document_service: DocumentService = Depends(get_document_service)
    ):
        """특정 문서 삭제"""
        try:
            success = await document_service.delete_document(document_id)
            if success:
                return DocumentDeleteResponse(
                    message=f"문서 {document_id}가 삭제되었습니다.",
                    document_id=document_id
                )
            else:
                raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")
        except HTTPException:
            raise
        except Exception as e:
            raise handle_router_error(e, "Document deletion", 500, "문서 삭제 중 오류가 발생했습니다.")
    
    return router


def create_chat_router() -> APIRouter:
    """채팅 라우터 생성"""
    router = APIRouter(prefix="/api/v1/chat", tags=["chat"])
    
    @router.post("", response_model=QueryResponse)
    async def chat(
        request: QueryRequest,
        rag_service: RAGService = Depends(get_rag_service)
    ):
        """
        RAG 기반 질의 응답 (Chat)
        
        - **query**: 검색할 질문
        - **top_k**: 반환할 관련 문서 개수 (기본값: 5)
        """
        try:
            # QueryRequest의 validator가 이미 query 검증을 수행
            result = await rag_service.query(request.query, top_k=request.top_k)
            return QueryResponse(**result)
        except Exception as e:
            raise handle_router_error(e, "Query processing", 500, "질의 처리 중 오류가 발생했습니다.")
    
    @router.post("/document", response_model=DebugQueryResponse)
    async def chat_with_document_debug(
        request: QueryRequest,
        rag_service: RAGService = Depends(get_rag_service)
    ):
        """
        RAG 기반 질의 응답 (디버깅용 - 어떤 문서를 검색하는지 확인)
        
        질문하면 어떤 문서를 검색하는지 디버깅용 엔드포인트입니다.
        검색된 문서의 상세 정보를 포함하여 반환합니다.
        
        - **query**: 검색할 질문
        - **top_k**: 반환할 관련 문서 개수 (기본값: 5)
        """
        try:
            # QueryRequest의 validator가 이미 query 검증을 수행
            # 서비스를 통한 디버깅 정보 포함 쿼리 처리
            result = await rag_service.query_with_debug_info(
                request.query,
                top_k=request.top_k
            )
            
            return DebugQueryResponse(**result)
        except Exception as e:
            raise handle_router_error(e, "Query processing", 500, "질의 처리 중 오류가 발생했습니다.")
    
    return router


def create_system_router() -> APIRouter:
    """시스템 라우터 생성 (루트, 헬스체크)"""
    router = APIRouter(tags=["system"])
    
    @router.get("/", tags=["system"])
    async def root():
        """루트 엔드포인트"""
        return JSONResponse(
            content={
                "message": "RAG System API",
                "status": "running",
                "version": "1.0.0"
            }
        )
    
    @router.get("/health", tags=["system"])
    async def health_check():
        """헬스 체크 엔드포인트"""
        return JSONResponse(
            content={
                "status": "healthy",
                "service": "RAG System API"
            }
        )
    
    return router

