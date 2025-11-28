"""
RAG 파이프라인

RAG (Retrieval-Augmented Generation) 파이프라인 로직을 관리합니다.
"""
from typing import List, Optional, Dict, Any
import logging
import re

from src.models.search_result import SearchResult
from src.repositories.vector_repository import VectorRepository
from src.services.prompt import RAGPromptTemplate
from src.managers import QwenManager

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    RAG 파이프라인
    
    검색(Retrieval)과 생성(Generation) 단계를 관리합니다.
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
        self.prompt_template = RAGPromptTemplate()
    
    async def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        검색 단계: 관련 문서 검색
        
        Args:
            query: 사용자 질문
            top_k: 검색할 문서 개수
            
        Returns:
            검색 결과 리스트
            
        Raises:
            ValueError: query가 비어있는 경우
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        
        logger.info("Starting document search with query: " + query + ", top_k: " + str(top_k))
        
        search_results = await self.vector_repository.search_similar(query, top_k=top_k)
        
        results_count = len(search_results)
        logger.info("Search completed with documents found: " + str(results_count))
        return search_results
    
    async def generate(
        self,
        query: str,
        contexts: List[str],
        use_llm: bool = True,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        생성 단계: 컨텍스트를 기반으로 답변 생성
        
        Args:
            query: 사용자 질문
            contexts: 관련 문서 컨텍스트 리스트
            use_llm: LLM 사용 여부 (False면 간단한 응답 생성)
            system_prompt: 커스텀 시스템 프롬프트
            
        Returns:
            생성된 답변
        """
        if not contexts:
            return "제공된 문서에서 질문과 관련된 정보를 찾을 수 없습니다."
        
        # 컨텍스트 품질 재검증
        valid_contexts = [
            ctx for ctx in contexts 
            if ctx and ctx.strip() and len(ctx.strip()) >= 20
        ]
        
        if not valid_contexts:
            return "제공된 문서에서 질문과 관련된 유용한 정보를 찾을 수 없습니다."
        
        if use_llm and self.llm_manager:
            # LLM 모델이 아직 초기화되지 않았으면 초기화
            if not self.llm_manager.model_loader.is_loaded():
                logger.info("Initializing LLM model for first use")
                self.llm_manager.initialize()
            
            # LLM을 사용한 답변 생성
            logger.info("Generating answer using LLM with contexts count: " + str(len(valid_contexts)))
            try:
                answer = await self.llm_manager.generate_with_context(
                    query=query,
                    contexts=valid_contexts,
                    system_prompt=system_prompt or self.prompt_template.get_system_prompt(),
                    max_tokens=500  # 반복 방지를 위해 토큰 수 제한
                )
                
                logger.info("LLM generated answer (before post-processing), length: " + str(len(answer) if answer else 0))
                
                # 답변 후처리 및 품질 검증
                from src.utils.text_quality import post_process_answer, validate_answer_quality
                
                # 원본 답변 보존
                answer_before_validation = answer
                
                # 반복 제거만 수행 (길이 제한은 완화)
                answer = post_process_answer(answer, max_length=1000)  # 길이 제한 완화
                logger.info("Answer after post-processing, length: " + str(len(answer) if answer else 0))
                
                # 답변 품질 검증 (컨텍스트 일치도 확인 포함)
                # 작은 LLM 모델의 특성을 고려하여 검증 완화
                # "문서에 없다"고 말하는 답변이지만 실제로는 관련 정보가 있는 경우 특별 처리
                has_negative_phrase = any(phrase in answer for phrase in ['없', '찾을 수 없', '포함되어 있지 않', '설명이 없다', '정보가 없다'])
                
                if has_negative_phrase:
                    # 컨텍스트에 질문 관련 키워드가 있는지 확인
                    query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
                    context_text_lower = " ".join(valid_contexts).lower()
                    context_has_keywords = any(keyword in context_text_lower for keyword in query_keywords if len(keyword) > 1)
                    
                    if context_has_keywords:
                        # 컨텍스트에 관련 정보가 있는데 "없다"고 말하는 경우, 품질 검증 실패로 간주
                        logger.warning("LLM claims information not found but context contains relevant keywords")
                        logger.warning("Original answer (first 200 chars): " + (answer_before_validation[:200] if answer_before_validation else "None"))
                        logger.warning("Falling back to simple response")
                        answer = self.prompt_template.build_simple_response(query, valid_contexts)
                    else:
                        # 정말 관련 정보가 없는 경우, 품질 검증 통과
                        is_valid, error_msg = validate_answer_quality(
                            answer, 
                            min_length=10, 
                            max_length=2000,  # 길이 제한 완화
                            contexts=valid_contexts
                        )
                        if not is_valid:
                            logger.warning("LLM generated answer quality check failed: " + (error_msg or "Unknown error"))
                            answer = self.prompt_template.build_simple_response(query, valid_contexts)
                        else:
                            logger.info("LLM answer quality check passed, using LLM answer")
                else:
                    # 일반 답변의 경우 품질 검증 (작은 모델 특성 고려하여 완화)
                    is_valid, error_msg = validate_answer_quality(
                        answer, 
                        min_length=10, 
                        max_length=2000,  # 길이 제한 완화
                        contexts=valid_contexts
                    )
                    if not is_valid:
                        # 품질 검증 실패 시, 원본 답변을 한 번 더 확인
                        # 원본 답변이 반복이 없고 최소 길이를 만족하면 사용
                        if answer_before_validation and len(answer_before_validation.strip()) >= 10:
                            from src.utils.text_quality import detect_repetition
                            if not detect_repetition(answer_before_validation):
                                logger.info("Using original answer despite quality check failure (small LLM model consideration)")
                                answer = answer_before_validation
                            else:
                                logger.warning("LLM generated answer quality check failed: " + (error_msg or "Unknown error"))
                                logger.warning("Original answer (first 200 chars): " + (answer_before_validation[:200] if answer_before_validation else "None"))
                                logger.warning("Falling back to simple response")
                                answer = self.prompt_template.build_simple_response(query, valid_contexts)
                        else:
                            logger.warning("LLM generated answer quality check failed: " + (error_msg or "Unknown error"))
                            logger.warning("Falling back to simple response")
                            answer = self.prompt_template.build_simple_response(query, valid_contexts)
                    else:
                        logger.info("LLM answer quality check passed, using LLM answer")
            except Exception as e:
                logger.error("LLM generation failed with exception: " + str(e))
                import traceback
                logger.error("Traceback: " + traceback.format_exc())
                logger.error("Falling back to simple response")
                answer = self.prompt_template.build_simple_response(query, valid_contexts)
        else:
            # 간단한 응답 생성 (LLM 없이)
            logger.info("Generating simple response without LLM with contexts count: " + str(len(valid_contexts)))
            answer = self.prompt_template.build_simple_response(query, valid_contexts)
        
        return answer
    
    async def run(
        self,
        query: str,
        top_k: int = 5,
        use_llm: bool = True,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        RAG 파이프라인 실행
        
        전체 파이프라인:
        1. 검색(Retrieval): 관련 문서 검색
        2. 생성(Generation): 검색된 문서를 기반으로 답변 생성
        
        Args:
            query: 사용자 질문
            top_k: 검색할 문서 개수
            use_llm: LLM 사용 여부
            system_prompt: 커스텀 시스템 프롬프트
            
        Returns:
            RAG 결과 딕셔너리
            - query: 사용자 질문
            - answer: 생성된 답변
            - contexts: 관련 문서 컨텍스트 리스트
            - sources: 검색 결과 소스 정보
            - top_k: 사용된 top_k 값
            
        Raises:
            ValueError: query가 비어있거나 top_k가 유효하지 않은 경우
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")
        
        logger.info("Starting RAG pipeline with query: " + query + ", top_k: " + str(top_k) + ", use_llm: " + str(use_llm))
        
        # 1. 검색 단계
        search_results = await self.retrieve(query, top_k)
        
        if not search_results:
            logger.warning("No relevant documents found for query: " + query)
            return {
                "query": query,
                "answer": "관련된 문서를 찾을 수 없습니다.",
                "contexts": [],
                "sources": [],
                "top_k": top_k
            }
        
        # 2. 컨텍스트 추출 및 관련성 필터링
        # 점수 임계값 적용 (관련성이 낮은 결과 제외)
        MIN_RELEVANCE_SCORE = 0.5  # 최소 관련성 점수 (0.3 -> 0.5로 상향)
        filtered_results = [
            result for result in search_results 
            if result.text and result.text.strip() and result.score >= MIN_RELEVANCE_SCORE
        ]
        
        if not filtered_results:
            logger.warning("No relevant documents found after filtering by score threshold for query: " + query)
            return {
                "query": query,
                "answer": "제공된 문서에서 질문과 관련된 정보를 찾을 수 없습니다. 다른 질문을 시도해주세요.",
                "contexts": [],
                "sources": [],
                "top_k": top_k
            }
        
        contexts = [result.text for result in filtered_results]
        
        # 컨텍스트 품질 검증 (너무 짧거나 의미 없는 컨텍스트 제외)
        MIN_CONTEXT_LENGTH = 20  # 최소 컨텍스트 길이
        valid_contexts = [
            ctx for ctx in contexts 
            if len(ctx.strip()) >= MIN_CONTEXT_LENGTH and not ctx.strip().startswith(".")
        ]
        
        if not valid_contexts:
            logger.warning("No valid contexts found after quality filtering for query: " + query)
            return {
                "query": query,
                "answer": "제공된 문서에서 질문과 관련된 유용한 정보를 찾을 수 없습니다.",
                "contexts": [],
                "sources": filtered_results,
                "top_k": top_k
            }
        
        # 3. 생성 단계
        answer = await self.generate(
            query=query,
            contexts=valid_contexts,
            use_llm=use_llm,
            system_prompt=system_prompt
        )
        
        result = {
            "query": query,
            "answer": answer,
            "contexts": valid_contexts,
            "sources": filtered_results,
            "top_k": top_k
        }
        
        logger.info("RAG pipeline completed for query: " + query)
        return result

