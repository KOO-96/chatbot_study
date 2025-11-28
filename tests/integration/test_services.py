"""
서비스 통합 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil

from src.services.document_service import DocumentService
from src.services.file_service import FileService
from src.services.rag_service import RAGService


@pytest.fixture
def temp_dir():
    """임시 디렉토리"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    if temp_path.exists():
        shutil.rmtree(temp_path, ignore_errors=True)


class TestDocumentService:
    """DocumentService 테스트"""
    
    @pytest.mark.asyncio
    async def test_upload_document_success(self, temp_dir, mock_vector_repository):
        """문서 업로드 성공"""
        # Mock 설정
        mock_vector_repository.save_chunks = AsyncMock(return_value="test-doc-id")
        
        # FileService는 실제로 사용 (간단한 텍스트 파일)
        file_service = FileService()
        service = DocumentService(mock_vector_repository, file_service)
        
        # 테스트 파일 생성
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a test document with some content.", encoding="utf-8")
        
        # 문서 업로드
        document = await service.upload_document(
            file_path=test_file,
            filename="test.txt",
            file_type="txt"
        )
        
        assert document.document_id is not None
        assert document.metadata.filename == "test.txt"
        assert document.chunks_count > 0
        mock_vector_repository.save_chunks.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_upload_document_empty_file(self, temp_dir, mock_vector_repository):
        """빈 파일 업로드"""
        file_service = FileService()
        service = DocumentService(mock_vector_repository, file_service)
        
        # 빈 파일 생성
        test_file = temp_dir / "empty.txt"
        test_file.write_text("", encoding="utf-8")
        
        # 빈 파일은 ValueError 발생
        with pytest.raises(ValueError, match="텍스트를 추출할 수 없습니다"):
            await service.upload_document(
                file_path=test_file,
                filename="empty.txt",
                file_type="txt"
            )
    
    @pytest.mark.asyncio
    async def test_list_all_documents(self, mock_vector_repository):
        """문서 목록 조회"""
        mock_vector_repository.find_all_documents = AsyncMock(return_value=[])
        
        file_service = FileService()
        service = DocumentService(mock_vector_repository, file_service)
        
        documents = await service.list_all_documents()
        
        assert isinstance(documents, list)
        mock_vector_repository.find_all_documents.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_document(self, mock_vector_repository):
        """문서 삭제"""
        mock_vector_repository.delete_by_document_id = AsyncMock(return_value=True)
        
        file_service = FileService()
        service = DocumentService(mock_vector_repository, file_service)
        
        result = await service.delete_document("test-id")
        
        assert result is True
        mock_vector_repository.delete_by_document_id.assert_called_once_with("test-id")


class TestRAGService:
    """RAGService 테스트"""
    
    @pytest.mark.asyncio
    async def test_query_success(self, mock_vector_repository):
        """쿼리 성공"""
        mock_vector_repository.search_similar = AsyncMock(return_value=[])  # 올바른 메서드명
        
        service = RAGService(mock_vector_repository)
        
        result = await service.query("test query", top_k=5)
        
        assert "query" in result
        assert "answer" in result
        assert "contexts" in result
        assert "sources" in result
    
    @pytest.mark.asyncio
    async def test_query_with_debug_info(self, mock_vector_repository):
        """디버깅 정보 포함 쿼리"""
        # Mock search results - SearchResult 객체 생성
        from src.models.search_result import SearchResult
        from src.models.chunk import ChunkMetadata
        
        mock_metadata = ChunkMetadata(
            document_id="doc1",
            chunk_index=0,
            filename="test.pdf",
            file_type="pdf"
        )
        mock_result = SearchResult(
            text="test text",
            score=0.9,
            metadata=mock_metadata
        )
        
        mock_vector_repository.search_similar = AsyncMock(return_value=[mock_result])  # 올바른 메서드명
        
        service = RAGService(mock_vector_repository)
        
        result = await service.query_with_debug_info("test query", top_k=5)
        
        assert "debug_info" in result
        assert "searched_documents" in result["debug_info"]
        assert result["debug_info"]["total_documents_found"] >= 0

