"""
파일 처리 서비스

새로운 아키텍처에 따라 파일을 처리합니다:
1. PDF/TXT 파일을 processors로 처리하여 Markdown으로 변환
2. Markdown을 chunker로 분할
3. Chunk 모델 생성
"""
from pathlib import Path
from typing import List
import logging
import tempfile
import shutil

from src.models.chunk import Chunk, ChunkMetadata
from src.settings import settings
from src.utils import validate_file_extension, save_uploaded_file, cleanup_temp_file, get_file_name
from src.processors import PDFProcessor, TXTProcessor, MarkdownBuilder, Merger
from src.utils.chunker import MarkdownChunker

logger = logging.getLogger(__name__)


class FileService:
    """
    파일 처리 서비스
    
    PDF 및 TXT 파일을 처리하여 Markdown으로 변환하고,
    의미 있는 단위로 청크를 분할합니다.
    """
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        """
        Args:
            chunk_size: 청크 크기 (문자 수, 기본값: 설정값)
            chunk_overlap: 청크 간 겹치는 문자 수 (기본값: 설정값)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        # Processors 초기화
        self.pdf_processor = PDFProcessor()
        self.txt_processor = TXTProcessor()
        self.markdown_builder = MarkdownBuilder()
        self.merger = Merger()
        
        # Chunker 초기화
        self.chunker = MarkdownChunker(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )
    
    def process_file(
        self,
        file_path: Path,
        document_id: str,
        filename: str,
        file_type: str
    ) -> List[Chunk]:
        """
        파일 처리 및 청크 생성
        
        비즈니스 로직:
        1. 파일 타입에 따라 PDF/TXT 프로세서로 처리
        2. Markdown 형식으로 변환
        3. Markdown을 의미 있는 단위로 청크 분할
        4. 각 청크에 메타데이터 추가하여 Chunk 모델 생성
        
        Args:
            file_path: 처리할 파일 경로
            document_id: 문서 ID
            filename: 파일명
            file_type: 파일 타입 (pdf, txt)
            
        Returns:
            청크 모델 리스트 (텍스트가 없으면 빈 리스트)
            
        Raises:
            FileNotFoundError: 파일이 존재하지 않는 경우
        """
        if not file_path.exists():
            raise FileNotFoundError("File not found: " + str(file_path))
        
        logger.info("Starting file processing: " + filename)
        
        # 1. 파일 타입에 따라 Markdown으로 변환
        markdown_content = self._process_to_markdown(file_path, file_type)
        
        if not markdown_content or not markdown_content.strip():
            file_name = get_file_name(file_path, filename)
            logger.warning(f"Cannot extract content from file: {file_name}")
            return []
        
        markdown_length = len(markdown_content)
        logger.info("Markdown conversion completed - length: " + str(markdown_length))
        
        # 2. Markdown을 청크로 분할
        chunk_dicts = self.chunker.chunk_markdown(markdown_content)
        chunks_count = len(chunk_dicts)
        logger.info("Markdown chunking completed - chunks count: " + str(chunks_count))
        
        # 3. 청크 모델로 변환
        chunks = []
        for i, chunk_dict in enumerate(chunk_dicts):
            chunk = Chunk(
                text=chunk_dict["text"],
                metadata=ChunkMetadata(
                    document_id=document_id,
                    chunk_index=i,
                    filename=filename,
                    file_type=file_type
                )
            )
            chunks.append(chunk)
        
        final_chunks_count = len(chunks)
        logger.info("File processing completed - filename: " + filename + ", chunks count: " + str(final_chunks_count))
        return chunks
    
    def _process_to_markdown(self, file_path: Path, file_type: str) -> str:
        """
        파일을 Markdown 형식으로 변환
        
        Args:
            file_path: 파일 경로
            file_type: 파일 타입 (pdf, txt)
            
        Returns:
            Markdown 형식의 텍스트
        """
        if file_type.lower() == "pdf":
            return self._process_pdf(file_path)
        elif file_type.lower() == "txt":
            return self._process_txt(file_path)
        else:
            raise ValueError("Unsupported file type: " + file_type)
    
    def _process_pdf(self, file_path: Path) -> str:
        """
        PDF 파일을 Markdown으로 변환
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            Markdown 형식의 텍스트
        """
        temp_image_dir = None
        try:
            # 텍스트 추출
            text = self.pdf_processor.extract_text(file_path)
            
            # 테이블 추출
            tables = self.pdf_processor.extract_tables(file_path)
            
            # 이미지 추출 (임시 디렉토리 사용)
            temp_image_dir = Path(tempfile.mkdtemp())
            try:
                images = self.pdf_processor.extract_images(file_path, temp_image_dir)
            except Exception as e:
                logger.warning("Image extraction failed, continuing without images: " + str(e))
                images = []
            
            # Markdown으로 통합
            markdown = self.markdown_builder.build_pdf_markdown(
                text=text,
                tables=tables,
                images=images
            )
            
            return markdown
        
        except Exception as e:
            file_name = get_file_name(file_path)
            logger.error(f"PDF processing failed - filename: {file_name}, error: {str(e)}")
            raise
        
        finally:
            # 임시 이미지 디렉토리 정리
            if temp_image_dir and temp_image_dir.exists():
                try:
                    shutil.rmtree(temp_image_dir)
                    logger.debug("Temporary image directory cleaned up: " + str(temp_image_dir))
                except Exception as e:
                    logger.warning("Failed to cleanup temporary image directory: " + str(temp_image_dir) + ", error: " + str(e))
    
    def _process_txt(self, file_path: Path) -> str:
        """
        TXT 파일을 Markdown으로 변환
        
        Args:
            file_path: TXT 파일 경로
            
        Returns:
            Markdown 형식의 텍스트
        """
        try:
            # TXT 정규화 (Markdown 형식으로 변환)
            markdown = self.txt_processor.normalize(file_path)
            return markdown
        
        except Exception as e:
            file_name = get_file_name(file_path)
            logger.error(f"TXT processing failed - filename: {file_name}, error: {str(e)}")
            raise
