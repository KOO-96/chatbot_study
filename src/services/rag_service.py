from typing import Optional, Dict, Any, List
import logging

from src.repositories.vector_repository import VectorRepository
from src.services.pipeline import RAGPipeline
from src.managers import QwenManager
from src.models.search_result import SearchResult

logger = logging.getLogger(__name__)


class RAGService:
    """
    RAG (Retrieval-Augmented Generation) 서비스
    
    사용자 질문에 대해 벡터 검색을 통해 관련 문서를 찾고,
    찾은 컨텍스트를 기반으로 답변을 생성합니다.
    """
    
    def __init__(
        self,
        vector_repository: VectorRepository,
        llm_manager: Optional[QwenManager] = None
    ):
        """
        Args:
            vector_repository: 벡터 리포지토리 인스턴스
            llm_manager: LLM 관리자 (None이면 간단한 응답 생성)
        """
        self.vector_repository = vector_repository
        self.llm_manager = llm_manager
        self.pipeline = RAGPipeline(vector_repository, llm_manager)
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        use_llm: bool = True  # 기본값을 True로 변경하여 LLM 사용 권장
    ) -> dict:
        """
        RAG 기반 질의 응답 처리
        
        비즈니스 로직:
        1. 사용자 질문을 벡터로 변환하여 유사한 문서 검색
        2. 검색된 문서에서 컨텍스트 추출
        3. 컨텍스트를 기반으로 답변 생성
        
        Args:
            query: 사용자 질문
            top_k: 검색할 관련 문서 개수 (기본값: 5)
            use_llm: LLM 사용 여부 (기본값: False)
            
        Returns:
            질의 응답 결과 딕셔너리
            - query: 사용자 질문
            - answer: 생성된 답변
            - contexts: 관련 문서 컨텍스트 리스트
            - sources: 검색 결과 소스 정보
            - top_k: 사용된 top_k 값
        """
        logger.info("Starting RAG query processing with query: " + query + ", top_k: " + str(top_k) + ", use_llm: " + str(use_llm))
        
        # RAG 파이프라인 실행
        result = await self.pipeline.run(
            query=query,
            top_k=top_k,
            use_llm=use_llm
        )
        
        logger.info("RAG query processing completed for query: " + query)
        return result
    
    async def query_with_debug_info(
        self,
        query: str,
        top_k: int = 5,
        use_llm: bool = False
    ) -> Dict[str, Any]:
        """
        RAG 기반 질의 응답 처리 (디버깅 정보 포함)
        
        비즈니스 로직:
        1. 기본 RAG 쿼리 실행
        2. 검색된 문서 정보 집계 (문서별 청크 수, 점수 통계)
        
        Args:
            query: 사용자 질문
            top_k: 검색할 관련 문서 개수 (기본값: 5)
            use_llm: LLM 사용 여부 (기본값: False)
            
        Returns:
            질의 응답 결과 딕셔너리 (debug_info 포함)
        """
        # 기본 RAG 쿼리 실행
        result = await self.query(query, top_k=top_k, use_llm=use_llm)
        
        # 디버깅 정보 집계
        document_info = {}
        sources: List[SearchResult] = result.get("sources", []) or []
        
        for source in sources:
            if not isinstance(source, SearchResult):
                continue
            
            doc_id = source.metadata.document_id
            filename = source.metadata.filename or "Unknown"
            
            if doc_id not in document_info:
                document_info[doc_id] = {
                    "document_id": doc_id,
                    "filename": filename,
                    "chunks_found": 0,
                    "scores": []
                }
            
            document_info[doc_id]["chunks_found"] += 1
            document_info[doc_id]["scores"].append(source.score)
        
        # 점수 통계 계산
        for doc_id in document_info:
            scores = document_info[doc_id]["scores"]
            if scores:
                document_info[doc_id]["avg_score"] = sum(scores) / len(scores)
                document_info[doc_id]["max_score"] = max(scores)
                document_info[doc_id]["min_score"] = min(scores)
            else:
                document_info[doc_id]["avg_score"] = 0.0
                document_info[doc_id]["max_score"] = 0.0
                document_info[doc_id]["min_score"] = 0.0
            
            # 점수 리스트 제거 (응답에 포함하지 않음)
            del document_info[doc_id]["scores"]
        
        # 디버깅 정보 추가
        result["debug_info"] = {
            "searched_documents": list(document_info.values()),
            "total_documents_found": len(document_info)
        }
        
        return result

