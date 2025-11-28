"""
Chunker 테스트
"""
import pytest
from src.utils.chunker import MarkdownChunker


class TestMarkdownChunker:
    """MarkdownChunker 테스트"""
    
    def test_chunk_simple_text(self):
        """간단한 텍스트 청킹"""
        chunker = MarkdownChunker(chunk_size=50, chunk_overlap=10)
        markdown = "This is a test document with multiple sentences."
        
        chunks = chunker.chunk_markdown(markdown)
        
        assert len(chunks) > 0
        assert all("text" in chunk for chunk in chunks)
    
    def test_chunk_large_document(self):
        """큰 문서 청킹"""
        chunker = MarkdownChunker(chunk_size=100, chunk_overlap=20)
        # 큰 문서 생성
        markdown = "\n\n".join([f"Paragraph {i}" for i in range(100)])
        
        chunks = chunker.chunk_markdown(markdown)
        
        assert len(chunks) > 1  # 여러 청크로 분할되어야 함
    
    def test_chunk_overlap(self):
        """청크 오버랩 확인"""
        chunker = MarkdownChunker(chunk_size=50, chunk_overlap=10)
        markdown = "A" * 100  # 100자 텍스트
        
        chunks = chunker.chunk_markdown(markdown)
        
        if len(chunks) > 1:
            # 오버랩이 있는지 확인 (간접적으로)
            total_length = sum(len(chunk["text"]) for chunk in chunks)
            # 오버랩이 있으면 총 길이가 원본보다 길어야 함
            assert total_length >= len(markdown)
    
    def test_empty_markdown(self):
        """빈 마크다운 처리"""
        chunker = MarkdownChunker(chunk_size=50, chunk_overlap=10)
        chunks = chunker.chunk_markdown("")
        
        assert len(chunks) == 0
    
    def test_invalid_chunk_size(self):
        """유효하지 않은 chunk_size"""
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=0, chunk_overlap=10)
        
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=-1, chunk_overlap=10)
    
    def test_invalid_chunk_overlap(self):
        """유효하지 않은 chunk_overlap"""
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=100, chunk_overlap=100)  # overlap >= size
        
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=100, chunk_overlap=-1)  # negative overlap

