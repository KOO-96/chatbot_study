"""
TXT 파일 처리 모듈

TXT 파일을 정규화하여 Markdown 형식으로 변환합니다.
"""
from pathlib import Path
import logging
import re

from src.utils.helper import log_file_operation, get_file_name

logger = logging.getLogger(__name__)


class TXTProcessor:
    """TXT 파일 처리 클래스"""
    
    def __init__(self):
        """TXT 프로세서 초기화"""
        pass
    
    def normalize(self, file_path: Path, encoding: str = "utf-8") -> str:
        """
        TXT 파일을 정규화하여 Markdown 형식으로 변환
        
        Args:
            file_path: TXT 파일 경로
            encoding: 파일 인코딩 (기본값: utf-8)
            
        Returns:
            정규화된 Markdown 형식의 텍스트
        """
        try:
            # 파일 읽기
            with open(file_path, "r", encoding=encoding) as f:
                text = f.read()
            
            # 정규화 처리
            normalized_text = self._normalize_text(text)
            
            text_length = len(normalized_text)
            log_file_operation("normalization completed", file_path, level="debug")
            logger.debug(f"Text length: {text_length}")
            return normalized_text
        
        except UnicodeDecodeError:
            # UTF-8 실패 시 다른 인코딩 시도
            if encoding == "utf-8":
                try:
                    file_name = get_file_name(file_path)
                    logger.debug(f"UTF-8 failed, trying cp949 encoding: {file_name}")
                    return self.normalize(file_path, encoding="cp949")
                except Exception as e:
                    log_file_operation("normalization failed (cp949 attempt failed)", file_path, level="error")
                    logger.error(f"Error: {str(e)}")
                    raise
            else:
                log_file_operation("normalization failed (encoding failed)", file_path, level="error")
                raise
        
        except Exception as e:
            log_file_operation("normalization failed", file_path, level="error")
            logger.error(f"Error: {str(e)}")
            raise
    
    def _normalize_text(self, text: str) -> str:
        """
        텍스트 정규화
        
        - 연속된 공백 정리
        - 줄바꿈 정리
        - 특수 문자 처리
        
        Args:
            text: 원본 텍스트
            
        Returns:
            정규화된 텍스트
        """
        # 연속된 공백을 하나로
        text = re.sub(r" +", " ", text)
        
        # 연속된 줄바꿈을 두 개로 제한
        text = re.sub(r"\n{3,}", "\n\n", text)
        
        # 탭을 공백으로 변환
        text = text.replace("\t", " ")
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text

