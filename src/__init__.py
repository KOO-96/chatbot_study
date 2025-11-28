"""
Source package
"""
from .settings import settings, Settings
from .dependencies import (
    get_vector_repository,
    get_file_service,
    get_document_service,
    get_rag_service,
    cleanup_singletons
)
from .lifespan import lifespan

__all__ = [
    "settings",
    "Settings",
    "get_vector_repository",
    "get_file_service",
    "get_document_service",
    "get_rag_service",
    "cleanup_singletons",
    "lifespan"
]
