from typing import List, TYPE_CHECKING, Any
import logging
import uuid
from pathlib import Path

from src.models.document import Document, DocumentMetadata
from src.repositories.vector_repository import VectorRepository
from src.services.file_service import FileService
from src.settings import settings
from src.utils import (
    validate_file_extension,
    save_uploaded_file,
    cleanup_temp_file,
    sanitize_filename,
    extract_file_type
)

# FastAPI UploadFile은 타입 힌트에만 사용 (런타임 의존성 없음)
if TYPE_CHECKING:
    from fastapi import UploadFile
else:
    UploadFile = Any  # type: ignore

logger = logging.getLogger(__name__)


class DocumentService:
    """
    문서 관리 서비스
    
    문서 업로드, 조회, 삭제 등의 비즈니스 로직을 처리합니다.
    """
    
    def __init__(
        self,
        vector_repository: VectorRepository,
        file_service: FileService
    ):
        """
        Args:
            vector_repository: 벡터 리포지토리 인스턴스
            file_service: 파일 서비스 인스턴스
        """
        self.vector_repository = vector_repository
        self.file_service = file_service
    
    async def upload_document(
        self,
        file_path: Path,
        filename: str,
        file_type: str
    ) -> Document:
        """
        문서 업로드 및 벡터화 처리
        
        비즈니스 로직:
        1. 문서 ID 생성
        2. 파일에서 텍스트 추출 및 청크 분할
        3. 벡터화하여 저장
        4. 문서 메타데이터 생성
        
        Args:
            file_path: 업로드된 파일 경로
            filename: 파일명
            file_type: 파일 타입 (pdf, txt)
            
        Returns:
            생성된 문서 모델
            
        Raises:
            ValueError: 파일에서 텍스트를 추출할 수 없는 경우
        """
        # 1. 문서 ID 생성
        document_id = str(uuid.uuid4())
        logger.info("Starting document upload - filename: " + filename + ", document ID: " + document_id)
        
        # 2. 파일 처리 및 청크 생성
        chunks = self.file_service.process_file(
            file_path=file_path,
            document_id=document_id,
            filename=filename,
            file_type=file_type
        )
        
        if not chunks:
            raise ValueError("파일에서 텍스트를 추출할 수 없습니다.")
        
        # 3. 벡터화하여 저장
        await self.vector_repository.save_chunks(chunks)
        chunks_count = len(chunks)
        logger.info("Vector storage completed with chunks count: " + str(chunks_count))
        
        # 4. 문서 모델 생성
        document = Document(
            document_id=document_id,
            metadata=DocumentMetadata(
                filename=filename,
                file_type=file_type
            ),
            chunks_count=len(chunks)
        )
        
        logger.info("Document upload completed - filename: " + filename + ", document ID: " + document_id)
        return document
    
    async def list_all_documents(self) -> List[Document]:
        """
        모든 문서 목록 조회
        
        Returns:
            저장된 모든 문서 목록
        """
        documents = await self.vector_repository.find_all_documents()
        docs_count = len(documents)
        logger.info("Document list retrieval completed with documents count: " + str(docs_count))
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        """
        문서 삭제
        
        비즈니스 로직:
        1. 문서 ID로 벡터 저장소에서 해당 문서의 모든 청크 검색
        2. 검색된 청크들을 모두 삭제
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            삭제 성공 여부 (문서가 존재하지 않으면 False)
        """
        success = await self.vector_repository.delete_by_document_id(document_id)
        
        if success:
            logger.info("Document deleted successfully: " + document_id)
        else:
            logger.warning("Document not found: " + document_id)
        
        return success
    
    async def upload_file_from_request(self, file: UploadFile) -> Document:
        """
        업로드 요청에서 파일을 받아 문서 업로드 처리
        
        비즈니스 로직:
        1. 파일명 검증 및 sanitization
        2. 파일 확장자 검증
        3. 파일 저장
        4. 문서 업로드 및 벡터화
        5. 임시 파일 정리
        
        Args:
            file: FastAPI UploadFile 객체
            
        Returns:
            생성된 문서 모델
            
        Raises:
            ValueError: 파일명이 없거나 유효하지 않은 경우
            ValueError: 파일 확장자가 유효하지 않은 경우
        """
        # 파일명 검증
        if not file.filename:
            raise ValueError("파일명이 제공되지 않았습니다.")
        
        # 파일 확장자 검증
        if not validate_file_extension(file.filename):
            raise ValueError("지원하지 않는 파일 형식입니다. PDF 또는 TXT 파일만 업로드 가능합니다.")
        
        # 파일명 sanitization
        safe_filename = sanitize_filename(file.filename)
        
        # 파일 타입 추출
        try:
            file_type = extract_file_type(file.filename)
        except ValueError:
            raise ValueError("유효하지 않은 파일 확장자입니다.")
        
        file_path = None
        try:
            # 파일 저장 (file.file은 이미 열려있으므로 그대로 사용)
            # 파일 포인터를 처음으로 리셋 (이미 읽혔을 수 있음)
            if hasattr(file.file, 'seek'):
                file.file.seek(0)
            
            file_path = save_uploaded_file(
                file_content=file.file,
                save_path=settings.upload_dir / safe_filename,
                create_parent=True
            )
            
            logger.info("File saved from upload request: " + file.filename)
            
            # 문서 업로드 및 벡터화
            document = await self.upload_document(
                file_path=file_path,
                filename=safe_filename,
                file_type=file_type
            )
            
            return document
        
        finally:
            # 임시 파일 정리
            if file_path:
                cleanup_temp_file(file_path)

