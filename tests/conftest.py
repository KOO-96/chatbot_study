"""
Pytest configuration and shared fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Generator

# 테스트용 임시 디렉토리
TEST_TEMP_DIR = Path(tempfile.mkdtemp(prefix="rag_test_"))


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """테스트용 임시 디렉토리"""
    test_dir = Path(tempfile.mkdtemp(prefix="rag_test_"))
    yield test_dir
    # 정리
    if test_dir.exists():
        shutil.rmtree(test_dir, ignore_errors=True)


@pytest.fixture
def mock_settings(temp_dir: Path):
    """테스트용 설정 모킹"""
    from unittest.mock import patch
    from src.settings import Settings
    import uuid
    
    # 각 테스트마다 고유한 Qdrant 경로 사용 (동시 접근 문제 해결)
    unique_id = str(uuid.uuid4())[:8]
    test_settings = Settings(
        qdrant_path=str(temp_dir / f"qdrant_db_{unique_id}"),
        upload_dir=temp_dir / "uploads",
        cache_dir=str(temp_dir / f"models_cache_{unique_id}"),
        chunk_size=500,
        chunk_overlap=50,
        max_file_size_mb=10  # 테스트용 작은 크기
    )
    
    with patch("src.settings.settings", test_settings):
        yield test_settings


@pytest.fixture
def mock_upload_file():
    """Mock FastAPI UploadFile"""
    mock_file = Mock()
    mock_file.filename = "test.pdf"
    mock_file.file = Mock()
    mock_file.file.read = Mock(return_value=b"test content")
    mock_file.file.seek = Mock()
    return mock_file


@pytest.fixture
def sample_text_file(temp_dir: Path) -> Path:
    """샘플 텍스트 파일 생성"""
    test_file = temp_dir / "test.txt"
    test_file.write_text("This is a test document.\n\nIt has multiple paragraphs.", encoding="utf-8")
    return test_file


@pytest.fixture
def sample_pdf_content() -> bytes:
    """샘플 PDF 바이너리 (최소한의 유효한 PDF)"""
    # 최소한의 PDF 구조 (실제로는 더 복잡하지만 테스트용)
    return b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\nxref\n0 1\ntrailer\n<<\n/Root 1 0 R\n>>\n%%EOF"


@pytest.fixture
def mock_embedding_generator():
    """Mock EmbeddingGenerator"""
    mock_gen = Mock()
    mock_gen.initialize = Mock()
    mock_gen.generate_embeddings = Mock(return_value=[[0.1] * 384])  # 384차원 임베딩
    mock_gen.generate_embedding = Mock(return_value=[0.1] * 384)
    mock_gen.get_embedding_dimension = Mock(return_value=384)
    return mock_gen


@pytest.fixture
def mock_vector_repository():
    """Mock VectorRepository"""
    from unittest.mock import AsyncMock
    mock_repo = Mock()
    mock_repo.initialize = Mock()
    mock_repo.save_chunks = AsyncMock(return_value="test_doc_id")
    mock_repo.search_similar = AsyncMock(return_value=[])  # 올바른 메서드명
    mock_repo.find_all_documents = AsyncMock(return_value=[])
    mock_repo.delete_by_document_id = AsyncMock(return_value=True)
    return mock_repo


@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """각 테스트 후 임시 파일 정리"""
    yield
    # 테스트 후 정리 로직 (필요시)
    pass

