from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, model_validator
from pathlib import Path
from typing import Literal


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # Qdrant 설정
    qdrant_collection_name: str = "rag_documents"
    qdrant_path: str = "./qdrant_db"
    
    # 임베딩 모델 설정
    embedding_model: str = "intfloat/multilingual-e5-large-instruct"
    
    # LLM 모델 설정
    # 주의: Qwen3-VL은 Vision-Language 모델이므로 텍스트 전용 RAG에는 Qwen2.5-1.5B-Instruct 권장
    # Qwen3-VL을 사용하려면 이미지 입력이 필요할 수 있음
    # 사용 가능한 모델: Qwen2.5-1.5B-Instruct, Qwen2.5-3B-Instruct, Qwen2.5-7B-Instruct 등
    llm_model_name: str = "Qwen/Qwen2.5-1.5B-Instruct"  # 텍스트 전용 RAG에 적합 (가장 작은 모델)
    llm_device: str = "cpu"  # "cuda", "cpu", "auto"
    llm_load_in_8bit: bool = False
    llm_load_in_4bit: bool = False  # CPU 환경에서는 양자화 미지원 (CUDA 환경에서만 사용 가능)
    llm_trust_remote_code: bool = True
    cache_dir: str = "./models_cache"  # 모델 캐시 디렉토리
    
    # 파일 처리 설정
    chunk_size: int = Field(default=500, ge=100, le=2000)  # 100-2000 사이
    chunk_overlap: int = Field(default=50, ge=0, le=500)  # 0-500 사이
    upload_dir: Path = Path("uploads")
    max_file_size_mb: int = Field(default=100, ge=1, le=500)  # 1-500MB
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = Field(default=8000, ge=1024, le=65535)  # 1024-65535 사이
    
    @model_validator(mode="after")
    def validate_chunk_overlap(self) -> "Settings":
        """chunk_overlap이 chunk_size보다 작은지 확인"""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        return self
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings()

