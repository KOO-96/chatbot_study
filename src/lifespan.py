"""
애플리케이션 생명주기 관리

FastAPI의 startup/shutdown 이벤트를 관리합니다.
"""
from contextlib import asynccontextmanager
import logging
from pathlib import Path

from src.settings import settings
from src.dependencies import get_embedding_generator, get_vector_repository, cleanup_singletons
from src.managers.qwen import get_model_loader

logger = logging.getLogger(__name__)

# 선택적 의존성 (torch는 없을 수 있음)
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None


@asynccontextmanager
async def lifespan(app):
    """
    애플리케이션 생명주기 관리
    
    - Startup: EmbeddingGenerator, Qdrant 벡터 리포지토리 초기화, 디렉토리 생성
    - Shutdown: 리소스 정리
    """
    # Startup
    logger.info("Application starting...")
    
    try:
        # Embedding Generator 초기화 (싱글톤)
        embedding_generator = get_embedding_generator()
        logger.info("Embedding generator initialized")
        
        # Qdrant 벡터 리포지토리 초기화 (싱글톤)
        vector_repo = get_vector_repository()
        logger.info("Qdrant vector store initialized")
        
        # 업로드 디렉토리 생성
        settings.upload_dir.mkdir(exist_ok=True)
        upload_dir_str = str(settings.upload_dir)
        logger.info("Upload directory created: " + upload_dir_str)
        
        # 모델 캐시 디렉토리 생성
        Path(settings.cache_dir).mkdir(parents=True, exist_ok=True)
        logger.info("Model cache directory created: " + settings.cache_dir)
        
    except Exception as e:
        logger.error("Application startup failed: " + str(e))
        raise
    
    logger.info("Application startup completed")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    
    try:
        # 1. LLM 모델 캐시 정리
        try:
            model_loader = get_model_loader()
            if model_loader.is_loaded():
                model_loader.clear_cache()
                logger.info("LLM model cache cleared")
        except Exception as e:
            logger.warning("Failed to clear LLM model cache: " + str(e))
        
        # 2. 싱글톤 인스턴스 정리 (EmbeddingGenerator, VectorRepository)
        try:
            cleanup_singletons()
        except Exception as e:
            logger.warning("Failed to cleanup singletons: " + str(e))
        
        # 3. GPU 메모리 정리 (CUDA 사용 시)
        if TORCH_AVAILABLE and torch is not None:
            try:
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    logger.info("GPU memory cache cleared")
            except Exception as e:
                logger.warning("Failed to clear GPU cache: " + str(e))
        
        logger.info("Application shutdown completed - all resources cleaned up")
    
    except Exception as e:
        logger.error("Error during shutdown cleanup: " + str(e))
        # Shutdown 중 에러가 발생해도 계속 진행
