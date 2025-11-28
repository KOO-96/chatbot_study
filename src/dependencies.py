"""
의존성 주입 함수들

FastAPI의 Depends를 통해 사용할 의존성 함수들을 정의합니다.
"""
import threading
import logging
from src.services.document_service import DocumentService
from src.services.file_service import FileService
from src.services.rag_service import RAGService
from src.repositories.vector_repository import VectorRepository
from src.utils.embedding_generator import EmbeddingGenerator
from src.managers import QwenManager
from src.settings import settings

logger = logging.getLogger(__name__)

# Thread-safety를 위한 Lock
_embedding_generator_lock = threading.Lock()
_vector_repository_lock = threading.Lock()


def get_embedding_generator() -> EmbeddingGenerator:
    """EmbeddingGenerator 인스턴스 생성 (싱글톤 패턴, thread-safe)"""
    if not hasattr(get_embedding_generator, "_instance"):
        with _embedding_generator_lock:
            if not hasattr(get_embedding_generator, "_instance"):
                generator = EmbeddingGenerator(settings.embedding_model)
                generator.initialize()
                get_embedding_generator._instance = generator
    return get_embedding_generator._instance


def get_vector_repository() -> VectorRepository:
    """VectorRepository 인스턴스 생성 (싱글톤 패턴, thread-safe)"""
    if not hasattr(get_vector_repository, "_instance"):
        with _vector_repository_lock:
            if not hasattr(get_vector_repository, "_instance"):
                embedding_generator = get_embedding_generator()
                vector_repo = VectorRepository(
                    collection_name=settings.qdrant_collection_name,
                    qdrant_path=settings.qdrant_path,
                    embedding_generator=embedding_generator
                )
                vector_repo.initialize()
                get_vector_repository._instance = vector_repo
    return get_vector_repository._instance


def get_file_service() -> FileService:
    """FileService 인스턴스 생성"""
    return FileService()


def get_document_service() -> DocumentService:
    """DocumentService 인스턴스 생성"""
    vector_repo = get_vector_repository()
    file_service = get_file_service()
    return DocumentService(vector_repo, file_service)


def get_rag_service() -> RAGService:
    """RAGService 인스턴스 생성"""
    vector_repo = get_vector_repository()
    # LLM Manager 초기화 및 전달 (지연 로딩: 필요할 때만 모델 로드)
    llm_manager = QwenManager()
    # 모델은 실제 사용 시점에 초기화됨 (lazy loading)
    return RAGService(vector_repo, llm_manager)


def cleanup_singletons():
    """모든 싱글톤 인스턴스 정리"""
    try:
        # EmbeddingGenerator 정리
        if hasattr(get_embedding_generator, "_instance"):
            instance = get_embedding_generator._instance
            if instance is not None:
                instance.cleanup()
            get_embedding_generator._instance = None
        
        # VectorRepository 정리
        if hasattr(get_vector_repository, "_instance"):
            instance = get_vector_repository._instance
            if instance is not None:
                instance.cleanup()
            get_vector_repository._instance = None
        
        logger.info("All singleton instances cleaned up")
    except Exception as e:
        logger.error("Failed to cleanup singletons: " + str(e))
