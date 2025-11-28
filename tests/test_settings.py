"""
설정 검증 테스트
"""
import pytest
from pathlib import Path
from pydantic import ValidationError

from src.settings import Settings


class TestSettings:
    """Settings 검증 테스트"""
    
    def test_default_settings(self):
        """기본 설정값"""
        settings = Settings()
        assert settings.chunk_size == 500
        assert settings.chunk_overlap == 50
        assert settings.port == 8000
    
    def test_chunk_size_validation(self):
        """chunk_size 검증"""
        # 유효한 값
        settings = Settings(chunk_size=200)
        assert settings.chunk_size == 200
        
        # 너무 작은 값
        with pytest.raises(ValidationError):
            Settings(chunk_size=50)
        
        # 너무 큰 값
        with pytest.raises(ValidationError):
            Settings(chunk_size=3000)
    
    def test_chunk_overlap_validation(self):
        """chunk_overlap 검증"""
        # 유효한 값
        settings = Settings(chunk_size=500, chunk_overlap=100)
        assert settings.chunk_overlap == 100
        
        # chunk_size보다 크거나 같으면 에러 (ValidationError 또는 ValueError)
        with pytest.raises((ValueError, ValidationError), match="chunk_overlap"):
            Settings(chunk_size=500, chunk_overlap=500)
        
        with pytest.raises((ValueError, ValidationError), match="chunk_overlap"):
            Settings(chunk_size=500, chunk_overlap=600)
    
    def test_port_validation(self):
        """포트 검증"""
        # 유효한 포트
        settings = Settings(port=8080)
        assert settings.port == 8080
        
        # 너무 작은 포트
        with pytest.raises(ValidationError):
            Settings(port=100)
        
        # 너무 큰 포트
        with pytest.raises(ValidationError):
            Settings(port=70000)
    
    def test_max_file_size_validation(self):
        """최대 파일 크기 검증"""
        # 유효한 값
        settings = Settings(max_file_size_mb=50)
        assert settings.max_file_size_mb == 50
        
        # 너무 작은 값
        with pytest.raises(ValidationError):
            Settings(max_file_size_mb=0)
        
        # 너무 큰 값
        with pytest.raises(ValidationError):
            Settings(max_file_size_mb=1000)

