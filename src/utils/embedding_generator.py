"""
임베딩 생성 모듈

텍스트를 벡터로 변환하는 임베딩 생성기를 제공합니다.
E5-large, BGE, GTE 등의 모델을 지원합니다.
"""
from typing import List, Optional
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """임베딩 생성기 클래스"""
    
    def __init__(self, model_name: str):
        """
        Args:
            model_name: 임베딩 모델 이름 (예: "intfloat/multilingual-e5-large-instruct")
        """
        self.model_name = model_name
        self.model: Optional[SentenceTransformer] = None
        # E5 모델인지 확인 (instruction prefix 필요 여부)
        self.is_e5_model = "e5" in model_name.lower() and "instruct" in model_name.lower()
    
    def initialize(self):
        """임베딩 모델 초기화"""
        try:
            self.model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded: " + self.model_name)
        except Exception as e:
            logger.error("Embedding model loading failed - model: " + self.model_name + ", error: " + str(e))
            raise
    
    def generate_embeddings(
        self, 
        texts: List[str], 
        show_progress: bool = False,
        instruction_type: str = "passage"
    ) -> np.ndarray:
        """
        텍스트 리스트를 벡터로 변환
        
        Args:
            texts: 임베딩할 텍스트 리스트
            show_progress: 진행 상황 표시 여부
            instruction_type: E5 모델용 instruction 타입 ("query" 또는 "passage")
            
        Returns:
            임베딩 벡터 배열 (numpy.ndarray)
            
        Raises:
            ValueError: texts가 비어있는 경우
        """
        if not self.model:
            raise RuntimeError("Embedding generator is not initialized")
        
        if not texts:
            raise ValueError("Cannot generate embeddings for empty texts list")
        
        try:
            # E5 모델인 경우 instruction prefix 추가
            if self.is_e5_model:
                if instruction_type == "query":
                    texts = [f"query: {text}" for text in texts]
                else:  # passage
                    texts = [f"passage: {text}" for text in texts]
            
            embeddings = self.model.encode(texts, show_progress_bar=show_progress)
            texts_count = len(texts)
            logger.debug("Embeddings generated - texts count: " + str(texts_count))
            return embeddings
        except Exception as e:
            logger.error("Embedding generation failed: " + str(e))
            raise
    
    def generate_embedding(self, text: str, instruction_type: str = "query") -> np.ndarray:
        """
        단일 텍스트를 벡터로 변환
        
        Args:
            text: 임베딩할 텍스트
            instruction_type: E5 모델용 instruction 타입 ("query" 또는 "passage")
            
        Returns:
            임베딩 벡터 (numpy.ndarray)
            
        Raises:
            ValueError: text가 비어있는 경우
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")
        
        return self.generate_embeddings([text], instruction_type=instruction_type)[0]
    
    def get_embedding_dimension(self) -> int:
        """
        임베딩 벡터의 차원 반환
        
        Returns:
            임베딩 차원
        """
        if not self.model:
            raise RuntimeError("Embedding generator is not initialized")
        
        return self.model.get_sentence_embedding_dimension()
    
    def cleanup(self):
        """임베딩 모델 메모리 해제"""
        if self.model is not None:
            try:
                # SentenceTransformer 모델 정리
                del self.model
                self.model = None
                logger.info("Embedding model cleaned up: " + self.model_name)
            except Exception as e:
                logger.warning("Failed to cleanup embedding model: " + str(e))

