"""
파일 처리 유틸리티

파일 저장, 검증 등의 공통 기능을 제공합니다.
"""
from pathlib import Path
from typing import Optional
import logging
import shutil
import re
import os

from src.settings import settings

logger = logging.getLogger(__name__)

# 파일 크기 제한 (기본값 100MB, 설정에서 오버라이드 가능)
def get_max_file_size() -> int:
    """설정에서 최대 파일 크기 가져오기"""
    return settings.max_file_size_mb * 1024 * 1024


def sanitize_filename(filename: str) -> str:
    """
    파일명 sanitization (경로 조작 방지)
    
    Args:
        filename: 원본 파일명
        
    Returns:
        sanitized 파일명
    """
    if not filename:
        return "unnamed_file"
    
    # 경로 구분자 제거 및 경로 조작 방지
    filename = os.path.basename(filename)
    
    # 경로 구분자 완전 제거 (슬래시, 백슬래시)
    filename = filename.replace('/', '').replace('\\', '')
    
    # 위험한 문자 제거
    filename = re.sub(r'[<>:"|?*\x00-\x1f]', '', filename)
    
    # 연속된 점 제거 (.. 방지)
    filename = re.sub(r'\.{2,}', '.', filename)
    
    # 앞뒤 공백 및 점 제거
    filename = filename.strip('. ')
    
    # 빈 파일명 처리
    if not filename:
        return "unnamed_file"
    
    # 파일명 길이 제한 (255자)
    if len(filename) > 255:
        name, ext = os.path.splitext(filename)
        filename = name[:255 - len(ext)] + ext
    
    return filename


def validate_file_extension(filename: str, allowed_extensions: list[str] = [".pdf", ".txt"]) -> bool:
    """
    파일 확장자 검증
    
    Args:
        filename: 파일명
        allowed_extensions: 허용된 확장자 리스트
        
    Returns:
        허용된 확장자면 True, 아니면 False
    """
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in allowed_extensions


def save_uploaded_file(
    file_content,
    save_path: Path,
    create_parent: bool = True,
    max_size: int = None
) -> Path:
    """
    업로드된 파일을 저장
    
    Args:
        file_content: 파일 내용 (file-like object)
        save_path: 저장할 경로
        create_parent: 부모 디렉토리 생성 여부
        max_size: 최대 파일 크기 (바이트, None이면 설정값 사용)
        
    Returns:
        저장된 파일 경로
        
    Raises:
        ValueError: 파일 크기가 제한을 초과하는 경우
    """
    if max_size is None:
        max_size = get_max_file_size()
    
    # 경로 정규화 (경로 조작 방지)
    save_path = save_path.resolve()
    
    # 부모 디렉토리가 허용된 디렉토리인지 확인 (추가 보안)
    # 여기서는 기본적으로 resolve()로 처리
    
    if create_parent:
        save_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        total_size = 0
        with open(save_path, "wb") as buffer:
            while True:
                chunk = file_content.read(8192)  # 8KB씩 읽기
                if not chunk:
                    break
                
                total_size += len(chunk)
                if total_size > max_size:
                    # 파일 삭제
                    if save_path.exists():
                        save_path.unlink()
                    raise ValueError(f"File size exceeds maximum allowed size of {max_size / (1024 * 1024):.1f}MB")
                
                buffer.write(chunk)
        
        logger.info("File saved successfully - size: " + str(total_size) + " bytes")
        return save_path
    except ValueError:
        raise
    except Exception as e:
        # 파일 삭제 시도
        if save_path.exists():
            try:
                save_path.unlink()
            except (OSError, PermissionError) as cleanup_error:
                logger.warning("Failed to cleanup file after error: " + str(cleanup_error))
        logger.error("File saving failed: " + str(e))
        raise


def cleanup_temp_file(file_path: Optional[Path]) -> None:
    """
    임시 파일 삭제
    
    Args:
        file_path: 삭제할 파일 경로 (None이면 무시)
    """
    if file_path and file_path.exists():
        try:
            file_path.unlink()
            file_path_str = str(file_path)
            logger.debug("Temporary file deleted: " + file_path_str)
        except Exception as e:
            file_path_str = str(file_path)
            logger.warning("Temporary file deletion failed - path: " + file_path_str + ", error: " + str(e))

