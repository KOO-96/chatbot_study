"""
Markdown 빌더 모듈

PDF에서 추출한 텍스트, 테이블, 이미지를 Markdown 형식으로 통합합니다.
"""
from typing import List, Optional
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MarkdownBuilder:
    """Markdown 문서 빌더 클래스"""
    
    def __init__(self):
        """Markdown 빌더 초기화"""
        pass
    
    def build_pdf_markdown(
        self,
        text: str,
        tables: Optional[List[str]] = None,
        images: Optional[List[str]] = None
    ) -> str:
        """
        PDF 내용을 Markdown 형식으로 통합
        
        Args:
            text: 추출된 텍스트
            tables: Markdown 형식의 테이블 리스트
            images: Markdown 형식의 이미지 블록 리스트
            
        Returns:
            통합된 Markdown 문서
        """
        markdown_parts = []
        
        # 텍스트 추가
        if text and text.strip():
            markdown_parts.append(text)
        
        # 테이블 추가
        if tables:
            for table in tables:
                if table:
                    markdown_parts.append("\n\n" + table + "\n\n")
        
        # 이미지 추가
        if images:
            for image in images:
                if image:
                    markdown_parts.append("\n\n" + image + "\n\n")
        
        combined_markdown = "\n\n".join(markdown_parts)
        markdown_length = len(combined_markdown)
        logger.debug("PDF Markdown building completed - length: " + str(markdown_length))
        return combined_markdown
    
    def save_markdown(self, markdown_content: str, output_path: Path) -> Path:
        """
        Markdown 내용을 파일로 저장
        
        Args:
            markdown_content: Markdown 내용
            output_path: 저장할 파일 경로
            
        Returns:
            저장된 파일 경로
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            output_path_str = str(output_path)
            logger.debug("Markdown file saved: " + output_path_str)
            return output_path
        
        except Exception as e:
            output_path_str = str(output_path)
            logger.error("Markdown file saving failed - path: " + output_path_str + ", error: " + str(e))
            raise

