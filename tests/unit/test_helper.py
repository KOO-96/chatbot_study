"""
Helper 유틸리티 테스트
"""
import pytest
from pathlib import Path
from src.utils.helper import (
    get_file_name,
    get_file_extension,
    extract_file_type,
    safe_execute
)


class TestGetFileName:
    """파일명 추출 테스트"""
    
    def test_from_path(self):
        """Path에서 파일명 추출"""
        file_path = Path("/test/example.pdf")
        assert get_file_name(file_path=file_path) == "example.pdf"
    
    def test_from_filename(self):
        """파일명 문자열에서 추출"""
        assert get_file_name(filename="example.pdf") == "example.pdf"
    
    def test_priority(self):
        """파일명 우선순위 (filename > file_path)"""
        file_path = Path("/test/old.pdf")
        assert get_file_name(file_path=file_path, filename="new.pdf") == "new.pdf"
    
    def test_unknown(self):
        """알 수 없는 파일명"""
        assert get_file_name() == "unknown"


class TestGetFileExtension:
    """파일 확장자 추출 테스트"""
    
    def test_from_path(self):
        """Path에서 확장자 추출"""
        file_path = Path("test.pdf")
        assert get_file_extension(file_path) == ".pdf"
    
    def test_from_string(self):
        """문자열에서 확장자 추출"""
        assert get_file_extension("test.txt") == ".txt"
    
    def test_no_extension(self):
        """확장자 없음"""
        assert get_file_extension("test") == ""
    
    def test_multiple_dots(self):
        """여러 점 처리"""
        assert get_file_extension("test.file.pdf") == ".pdf"


class TestExtractFileType:
    """파일 타입 추출 테스트"""
    
    def test_valid_extensions(self):
        """유효한 확장자"""
        assert extract_file_type("test.pdf") == "pdf"
        assert extract_file_type("test.txt") == "txt"
    
    def test_case_insensitive(self):
        """대소문자 무시"""
        assert extract_file_type("test.PDF") == "pdf"
        assert extract_file_type("test.TXT") == "txt"
    
    def test_no_extension(self):
        """확장자 없음"""
        with pytest.raises(ValueError):
            extract_file_type("test")
    
    def test_empty_string(self):
        """빈 문자열"""
        with pytest.raises(ValueError):
            extract_file_type("")


class TestSafeExecute:
    """안전한 실행 테스트"""
    
    def test_success(self):
        """성공 케이스"""
        def func():
            return "success"
        
        result = safe_execute(func, default="default")
        assert result == "success"
    
    def test_exception_with_default(self):
        """예외 발생 시 기본값 반환"""
        def func():
            raise ValueError("error")
        
        result = safe_execute(func, default="default")
        assert result == "default"
    
    def test_exception_without_default(self):
        """예외 발생 시 None 반환"""
        def func():
            raise ValueError("error")
        
        result = safe_execute(func)
        assert result is None

