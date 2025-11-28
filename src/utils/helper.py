"""
공통 헬퍼 함수

로깅, 에러 처리 등 공통 기능을 제공하여 코드 중복을 줄입니다.
"""
from pathlib import Path
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import logging

from fastapi import HTTPException

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ==================== 로깅 헬퍼 ====================

def log_file_operation(
    operation: str,
    file_path: Optional[Path] = None,
    filename: Optional[str] = None,
    level: str = "info"
):
    """
    파일 작업 로깅 헬퍼
    
    Args:
        operation: 작업 설명 (예: "completed", "failed")
        file_path: 파일 경로
        filename: 파일명 (file_path가 없을 때 사용)
        level: 로그 레벨 ("info", "error", "warning", "debug")
    """
    file_name = filename or (file_path.name if file_path else "unknown")
    log_func = getattr(logger, level.lower(), logger.info)
    log_func(f"File {operation} - filename: {file_name}")


def get_file_name(file_path: Optional[Path] = None, filename: Optional[str] = None) -> str:
    """
    파일명 추출 헬퍼
    
    Args:
        file_path: 파일 경로
        filename: 파일명
        
    Returns:
        파일명 문자열
    """
    if filename:
        return filename
    if file_path:
        return file_path.name
    return "unknown"


# ==================== 에러 처리 헬퍼 ====================

def handle_file_processing_error(
    file_path: Optional[Path] = None,
    filename: Optional[str] = None,
    operation: str = "processing"
):
    """
    파일 처리 에러 처리 데코레이터
    
    Args:
        file_path: 파일 경로
        filename: 파일명
        operation: 작업 설명
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            file_name = filename or (file_path.name if file_path else "unknown")
            try:
                return func(*args, **kwargs)
            except ValueError as e:
                logger.error(f"File {operation} validation error - filename: {file_name}, error: {str(e)}")
                raise
            except FileNotFoundError as e:
                logger.error(f"File {operation} not found - filename: {file_name}, error: {str(e)}")
                raise
            except Exception as e:
                logger.error(f"File {operation} failed - filename: {file_name}, error: {str(e)}")
                raise
        return wrapper
    return decorator


def safe_execute(
    func: Callable[..., T],
    default: Optional[T] = None,
    log_error: bool = True,
    error_message: Optional[str] = None
) -> Optional[T]:
    """
    안전한 함수 실행 (예외 발생 시 기본값 반환)
    
    Args:
        func: 실행할 함수
        default: 예외 발생 시 반환할 기본값
        log_error: 에러 로깅 여부
        error_message: 커스텀 에러 메시지
        
    Returns:
        함수 결과 또는 기본값
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            msg = error_message or f"Error executing {func.__name__}"
            logger.warning(f"{msg}: {str(e)}")
        return default


# ==================== 파일 확장자 헬퍼 ====================

def get_file_extension(file_path_or_name) -> str:
    """
    파일 확장자 추출 헬퍼
    
    Args:
        file_path_or_name: Path 객체 또는 파일명 문자열
        
    Returns:
        파일 확장자 (소문자, 점 포함, 예: ".pdf")
    """
    if isinstance(file_path_or_name, Path):
        return file_path_or_name.suffix.lower()
    return Path(str(file_path_or_name)).suffix.lower()


def extract_file_type(file_path_or_name) -> str:
    """
    파일 타입 추출 (확장자에서 점 제거)
    
    Args:
        file_path_or_name: Path 객체 또는 파일명 문자열
        
    Returns:
        파일 타입 (예: "pdf", "txt")
    """
    ext = get_file_extension(file_path_or_name)
    if not ext or len(ext) <= 1:
        raise ValueError("Invalid file extension")
    return ext[1:]  # .pdf -> pdf


# ==================== 라우터 에러 처리 헬퍼 ====================

def handle_router_error(
    error: Exception,
    operation: str,
    status_code: int = 500,
    detail: Optional[str] = None
) -> HTTPException:
    """
    라우터 에러 처리 헬퍼
    
    Args:
        error: 발생한 예외
        operation: 작업 설명
        status_code: HTTP 상태 코드
        detail: 커스텀 에러 메시지
        
    Returns:
        HTTPException
    """
    error_msg = detail or f"{operation} 중 오류가 발생했습니다."
    logger.error(f"{operation} error occurred: {str(error)}")
    return HTTPException(status_code=status_code, detail=error_msg)


def handle_file_upload_error(
    error: Exception,
    file_path: Optional[Path] = None,
    cleanup_func: Optional[Callable] = None
) -> HTTPException:
    """
    파일 업로드 에러 처리 헬퍼
    
    Args:
        error: 발생한 예외
        file_path: 임시 파일 경로
        cleanup_func: 정리 함수
        
    Returns:
        HTTPException
    """
    if isinstance(error, ValueError):
        error_msg = str(error)
        logger.error(f"File processing validation error: {error_msg}")
        if cleanup_func and file_path:
            cleanup_func(file_path)
        return HTTPException(status_code=400, detail=error_msg)
    
    if isinstance(error, FileNotFoundError):
        logger.error(f"File not found: {str(error)}")
        if cleanup_func and file_path:
            cleanup_func(file_path)
        return HTTPException(status_code=400, detail="파일을 찾을 수 없습니다.")
    
    error_msg = "파일 처리 중 오류가 발생했습니다."
    logger.error(f"File processing error occurred: {str(error)}")
    if cleanup_func and file_path:
        cleanup_func(file_path)
    return HTTPException(status_code=500, detail=error_msg)

