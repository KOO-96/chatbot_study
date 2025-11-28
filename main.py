from fastapi import FastAPI
import logging
import uvicorn

from src.routers import create_document_router, create_chat_router, create_system_router
from src import lifespan, settings

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="RAG System API",
    version="1.0.0",
    description="FastAPI 기반 RAG 시스템 - PDF/TXT 파일 업로드 및 벡터 검색",
    lifespan=lifespan
)

# 라우터 등록
app.include_router(create_system_router())
app.include_router(create_document_router())
app.include_router(create_chat_router())


if __name__ == "__main__":
    # uvicorn이 자동으로 SIGINT, SIGTERM을 처리하고
    # FastAPI의 lifespan이 shutdown 시 리소스 정리를 수행함
    import os
    from pathlib import Path
    
    # 모델 캐시 디렉토리와 Qdrant DB 디렉토리를 reload 감시에서 제외
    cache_dir = Path(settings.cache_dir).resolve()
    qdrant_dir = Path(settings.qdrant_path).resolve()
    
    # reload_excludes에 제외할 디렉토리 추가
    # 경로 패턴은 상대 경로 또는 절대 경로로 지정
    reload_excludes = [
        "models_cache/**",
        "qdrant_db/**",
        "**/models_cache/**",
        "**/qdrant_db/**",
        "**/*.pyc",
        "**/__pycache__/**",
        "**/.no_exist/**"  # HuggingFace 캐시의 .no_exist 디렉토리 제외
    ]
    
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        reload=True,
        reload_excludes=reload_excludes,  # 모델 캐시 디렉토리 제외
        log_level="info"
    )
