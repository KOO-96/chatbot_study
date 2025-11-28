"""
API 엔드포인트 통합 테스트
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import shutil

from main import app


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def temp_upload_dir():
    """임시 업로드 디렉토리"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)


class TestHealthCheck:
    """헬스 체크 테스트"""
    
    def test_health_endpoint(self, client):
        """헬스 체크 엔드포인트"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """루트 엔드포인트"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "status" in data


class TestDocumentEndpoints:
    """문서 엔드포인트 테스트"""
    
    @patch("src.routers.endpoint.get_document_service")
    def test_upload_document_success(self, mock_get_service, client, temp_upload_dir):
        """문서 업로드 성공"""
        # Mock 설정
        mock_service = Mock()
        mock_document = Mock()
        mock_document.metadata.filename = "test.pdf"
        mock_document.chunks_count = 5
        mock_document.document_id = "test-id"
        mock_service.upload_file_from_request = AsyncMock(return_value=mock_document)
        mock_get_service.return_value = mock_service
        
        # 파일 업로드
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}
        response = client.post("/api/v1/document", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert data["chunks_count"] == 5
        assert data["document_id"] == "test-id"
    
    def test_upload_document_no_file(self, client):
        """파일 없이 업로드"""
        response = client.post("/api/v1/document")
        assert response.status_code == 422  # Validation error
    
    @patch("src.routers.endpoint.get_document_service")
    def test_upload_document_invalid_extension(self, mock_get_service, client):
        """유효하지 않은 확장자"""
        mock_service = Mock()
        mock_service.upload_file_from_request = AsyncMock(
            side_effect=ValueError("지원하지 않는 파일 형식입니다.")
        )
        mock_get_service.return_value = mock_service
        
        files = {"file": ("test.exe", b"fake content", "application/x-msdownload")}
        response = client.post("/api/v1/document", files=files)
        
        assert response.status_code == 400
    
    @patch("src.routers.endpoint.get_document_service")
    def test_get_documents_info(self, mock_get_service, client):
        """문서 목록 조회"""
        mock_service = Mock()
        mock_service.list_all_documents = AsyncMock(return_value=[])
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/document/info")
        
        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total_count" in data
    
    @patch("src.routers.endpoint.get_document_service")
    def test_delete_document_success(self, mock_get_service, client):
        """문서 삭제 성공"""
        mock_service = Mock()
        mock_service.delete_document = AsyncMock(return_value=True)
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/v1/document/test-id")
        
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-id"
    
    @patch("src.routers.endpoint.get_document_service")
    def test_delete_document_not_found(self, mock_get_service, client):
        """문서 삭제 - 문서 없음"""
        mock_service = Mock()
        mock_service.delete_document = AsyncMock(return_value=False)
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/v1/document/nonexistent-id")
        
        assert response.status_code == 404


class TestChatEndpoints:
    """채팅 엔드포인트 테스트"""
    
    @patch("src.routers.endpoint.get_rag_service")
    def test_chat_success(self, mock_get_service, client):
        """채팅 성공"""
        mock_service = Mock()
        mock_service.query = AsyncMock(return_value={
            "query": "test query",
            "answer": "test answer",
            "contexts": ["context1", "context2"],
            "sources": [],
            "top_k": 5
        })
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/chat",
            json={"query": "test query", "top_k": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "test query"
        assert data["answer"] == "test answer"
    
    def test_chat_empty_query(self, client):
        """빈 질문"""
        response = client.post(
            "/api/v1/chat",
            json={"query": "   ", "top_k": 5}
        )
        
        assert response.status_code == 422  # Validation error
    
    @patch("src.routers.endpoint.get_rag_service")
    def test_chat_with_debug(self, mock_get_service, client):
        """디버깅 정보 포함 채팅"""
        mock_service = Mock()
        mock_service.query_with_debug_info = AsyncMock(return_value={
            "query": "test query",
            "answer": "test answer",
            "contexts": [],
            "sources": [],
            "top_k": 5,
            "debug_info": {
                "searched_documents": [],
                "total_documents_found": 0
            }
        })
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/chat/document",
            json={"query": "test query", "top_k": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "debug_info" in data

