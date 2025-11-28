"""
파일 유틸리티 테스트
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.utils.file_utils import (
    sanitize_filename,
    validate_file_extension,
    save_uploaded_file,
    cleanup_temp_file,
    get_max_file_size
)


class TestSanitizeFilename:
    """파일명 sanitization 테스트"""
    
    def test_normal_filename(self):
        """정상 파일명"""
        assert sanitize_filename("test.pdf") == "test.pdf"
        assert sanitize_filename("document.txt") == "document.txt"
    
    def test_dangerous_characters(self):
        """위험한 문자 제거"""
        assert sanitize_filename("test<file>.pdf") == "testfile.pdf"
        assert sanitize_filename("test:file.pdf") == "testfile.pdf"
        assert sanitize_filename("test|file.pdf") == "testfile.pdf"
    
    def test_path_traversal(self):
        """경로 조작 방지"""
        assert sanitize_filename("../test.pdf") == "test.pdf"
        assert sanitize_filename("../../etc/passwd") == "etcpasswd"
        assert sanitize_filename("..\\..\\test.pdf") == "test.pdf"
    
    def test_empty_filename(self):
        """빈 파일명 처리"""
        assert sanitize_filename("") == "unnamed_file"
        assert sanitize_filename(None) == "unnamed_file"
    
    def test_long_filename(self):
        """긴 파일명 처리"""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".pdf")


class TestValidateFileExtension:
    """파일 확장자 검증 테스트"""
    
    def test_valid_extensions(self):
        """유효한 확장자"""
        assert validate_file_extension("test.pdf") is True
        assert validate_file_extension("test.txt") is True
        assert validate_file_extension("test.PDF") is True  # 대소문자 무시
        assert validate_file_extension("test.TXT") is True
    
    def test_invalid_extensions(self):
        """유효하지 않은 확장자"""
        assert validate_file_extension("test.exe") is False
        assert validate_file_extension("test.doc") is False
        assert validate_file_extension("test") is False
    
    def test_empty_filename(self):
        """빈 파일명"""
        assert validate_file_extension("") is False
        assert validate_file_extension(None) is False
    
    def test_custom_allowed_extensions(self):
        """커스텀 허용 확장자"""
        assert validate_file_extension("test.docx", [".docx", ".doc"]) is True
        assert validate_file_extension("test.pdf", [".docx", ".doc"]) is False


class TestSaveUploadedFile:
    """파일 저장 테스트"""
    
    def test_save_file_success(self, temp_dir):
        """파일 저장 성공"""
        file_content = Mock()
        file_content.read = Mock(side_effect=[b"test content", b""])
        
        save_path = temp_dir / "test.txt"
        result = save_uploaded_file(
            file_content=file_content,
            save_path=save_path,
            create_parent=True
        )
        
        assert result == save_path
        assert save_path.exists()
        assert save_path.read_bytes() == b"test content"
    
    def test_file_size_limit(self, temp_dir):
        """파일 크기 제한"""
        file_content = Mock()
        # 큰 파일 시뮬레이션
        large_chunk = b"x" * 10240  # 10KB
        file_content.read = Mock(side_effect=[large_chunk, large_chunk, b""])
        
        save_path = temp_dir / "large.txt"
        
        with pytest.raises(ValueError, match="File size exceeds"):
            save_uploaded_file(
                file_content=file_content,
                save_path=save_path,
                max_size=1024  # 1KB 제한
            )
        
        # 파일이 삭제되었는지 확인
        assert not save_path.exists()
    
    def test_create_parent_directory(self, temp_dir):
        """부모 디렉토리 생성"""
        file_content = Mock()
        file_content.read = Mock(side_effect=[b"content", b""])
        
        save_path = temp_dir / "subdir" / "test.txt"
        result = save_uploaded_file(
            file_content=file_content,
            save_path=save_path,
            create_parent=True
        )
        
        assert save_path.parent.exists()
        assert result == save_path


class TestCleanupTempFile:
    """임시 파일 정리 테스트"""
    
    def test_cleanup_existing_file(self, temp_dir):
        """존재하는 파일 정리"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")
        
        cleanup_temp_file(test_file)
        
        assert not test_file.exists()
    
    def test_cleanup_nonexistent_file(self):
        """존재하지 않는 파일 정리 (에러 없음)"""
        nonexistent = Path("/nonexistent/file.txt")
        # 에러 없이 실행되어야 함
        cleanup_temp_file(nonexistent)
    
    def test_cleanup_none(self):
        """None 전달 (에러 없음)"""
        cleanup_temp_file(None)


class TestGetMaxFileSize:
    """최대 파일 크기 테스트"""
    
    @patch("src.utils.file_utils.settings")
    def test_get_max_file_size(self, mock_settings):
        """설정에서 최대 파일 크기 가져오기"""
        mock_settings.max_file_size_mb = 50
        result = get_max_file_size()
        assert result == 50 * 1024 * 1024  # 50MB in bytes

