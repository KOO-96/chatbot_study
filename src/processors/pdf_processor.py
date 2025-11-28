"""
PDF 처리 모듈

pdfplumber를 사용하여 PDF에서 텍스트와 테이블을 추출하고,
pypdfium2를 사용하여 이미지를 추출합니다.
이미지는 base64로 인코딩하여 Markdown에 포함합니다.
"""
from pathlib import Path
from typing import List, Optional
import logging
import base64
from io import BytesIO
import pdfplumber
import pypdfium2 as pdfium

from src.utils.helper import log_file_operation, get_file_name

logger = logging.getLogger(__name__)

# PDF 처리 제한
MAX_PDF_PAGES = 1000  # 최대 페이지 수
MAX_IMAGE_SIZE_MB = 5  # 이미지당 최대 크기 (MB)
MAX_IMAGES_PER_PDF = 100  # PDF당 최대 이미지 수


class PDFProcessor:
    """PDF 파일 처리 클래스"""
    
    def __init__(self):
        """PDF 프로세서 초기화"""
        pass
    
    def _validate_pdf_pages(self, total_pages: int) -> None:
        """
        PDF 페이지 수 검증
        
        Args:
            total_pages: 총 페이지 수
            
        Raises:
            ValueError: 페이지 수가 제한을 초과하는 경우
        """
        if total_pages > MAX_PDF_PAGES:
            raise ValueError(f"PDF has too many pages ({total_pages}). Maximum allowed: {MAX_PDF_PAGES}")
    
    def _open_pdf(self, file_path: Path):
        """
        PDF 파일 열기 (컨텍스트 매니저)
        
        Args:
            file_path: PDF 파일 경로
            
        Yields:
            pdfplumber.PDF 객체
        """
        return pdfplumber.open(file_path)
    
    def extract_text(self, file_path: Path) -> str:
        """
        PDF에서 텍스트 추출 (pdfplumber 사용)
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            추출된 텍스트
            
        Raises:
            ValueError: PDF 페이지 수가 제한을 초과하는 경우
        """
        try:
            text_parts = []
            with self._open_pdf(file_path) as pdf:
                total_pages = len(pdf.pages)
                self._validate_pdf_pages(total_pages)
                
                for page_num, page in enumerate(pdf.pages, 1):
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
            
            combined_text = "\n\n".join(text_parts)
            text_length = len(combined_text)
            log_file_operation("text extraction completed", file_path, level="debug")
            logger.debug(f"Text length: {text_length}")
            return combined_text
        
        except Exception as e:
            log_file_operation("text extraction failed", file_path, level="error")
            logger.error(f"Error: {str(e)}")
            raise
    
    def extract_tables(self, file_path: Path) -> List[str]:
        """
        PDF에서 테이블 추출 (pdfplumber 사용)
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            Markdown 형식의 테이블 리스트
        """
        try:
            markdown_tables = []
            with self._open_pdf(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            markdown_table = self._table_to_markdown(table)
                            if markdown_table:
                                markdown_tables.append(markdown_table)
            
            tables_count = len(markdown_tables)
            log_file_operation("table extraction completed", file_path, level="debug")
            logger.debug(f"Tables count: {tables_count}")
            return markdown_tables
        
        except Exception as e:
            log_file_operation("table extraction failed", file_path, level="error")
            logger.error(f"Error: {str(e)}")
            raise
    
    def extract_images(self, file_path: Path, output_dir: Optional[Path] = None) -> List[str]:
        """
        PDF에서 이미지 추출 (pypdfium2 사용)
        
        이미지는 base64로 인코딩하여 Markdown에 포함합니다.
        임시 파일 문제를 해결하기 위해 base64 인코딩을 사용합니다.
        
        Args:
            file_path: PDF 파일 경로
            output_dir: 이미지 저장 디렉토리 (사용하지 않음, 호환성을 위해 유지)
            
        Returns:
            Markdown 이미지 블록 리스트 (base64 인코딩)
        """
        pdf = None
        try:
            markdown_images = []
            pdf = pdfium.PdfDocument(file_path)
            
            total_pages = len(pdf)
            self._validate_pdf_pages(total_pages)
            
            for page_num in range(total_pages):
                if len(markdown_images) >= MAX_IMAGES_PER_PDF:
                    logger.warning(f"Maximum image limit reached ({MAX_IMAGES_PER_PDF}). Stopping extraction.")
                    break
                
                page = pdf.get_page(page_num)
                image_objects = page.get_images()
                
                for img_idx, image_obj in enumerate(image_objects):
                    if len(markdown_images) >= MAX_IMAGES_PER_PDF:
                        break
                    
                    try:
                        # 이미지 데이터 추출
                        image = image_obj.get_bitmap()
                        pil_image = image.to_pil()
                        
                        # 이미지를 base64로 인코딩
                        buffer = BytesIO()
                        pil_image.save(buffer, format="PNG")
                        image_bytes = buffer.getvalue()
                        
                        # 이미지 크기 확인
                        image_size_mb = len(image_bytes) / (1024 * 1024)
                        if image_size_mb > MAX_IMAGE_SIZE_MB:
                            logger.warning(f"Image too large ({image_size_mb:.2f}MB), skipping. Max: {MAX_IMAGE_SIZE_MB}MB")
                            continue
                        
                        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                        
                        # Markdown 이미지 블록 생성 (base64 데이터 URI 사용)
                        markdown_image = f"![Image](data:image/png;base64,{image_base64})"
                        markdown_images.append(markdown_image)
                        
                    except Exception as e:
                        logger.warning(f"Image extraction failed for page {page_num + 1}, image {img_idx + 1}, error: {str(e)}")
                        continue
            
            images_count = len(markdown_images)
            log_file_operation("image extraction completed", file_path, level="debug")
            logger.debug(f"Images count: {images_count}")
            return markdown_images
        
        except Exception as e:
            log_file_operation("image extraction failed", file_path, level="error")
            logger.error(f"Error: {str(e)}")
            raise
        
        finally:
            # PDF 파일 핸들 정리 (리소스 누수 방지)
            if pdf is not None:
                try:
                    pdf.close()
                except Exception as close_error:
                    logger.warning(f"Failed to close PDF document: {str(close_error)}")
    
    def _table_to_markdown(self, table: List[List]) -> str:
        """
        테이블 데이터를 Markdown 형식으로 변환
        
        Args:
            table: 2D 리스트 형태의 테이블 데이터
            
        Returns:
            Markdown 형식의 테이블 문자열
        """
        if not table or not table[0]:
            return ""
        
        # 헤더와 구분선 생성
        header = table[0]
        header_row = "| " + " | ".join(str(cell) if cell else "" for cell in header) + " |"
        separator = "| " + " | ".join(["---"] * len(header)) + " |"
        
        # 데이터 행 생성
        rows = [header_row, separator]
        for row in table[1:]:
            # 행 길이 맞추기
            padded_row = row + [""] * (len(header) - len(row))
            row_str = "| " + " | ".join(str(cell) if cell else "" for cell in padded_row[:len(header)]) + " |"
            rows.append(row_str)
        
        return "\n".join(rows)
