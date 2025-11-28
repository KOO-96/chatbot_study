"""
Markdown 기반 청킹 모듈

Markdown 문서를 의미 있는 단위로 분할합니다.
"""
from typing import List, Dict
import logging
import re

logger = logging.getLogger(__name__)


class MarkdownChunker:
    """Markdown 문서 청킹 클래스"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 겹치는 문자 수
            
        Raises:
            ValueError: chunk_size가 0 이하이거나 chunk_overlap이 chunk_size 이상인 경우
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk_markdown(self, markdown_content: str) -> List[Dict[str, str]]:
        """
        Markdown 문서를 청크로 분할
        
        Markdown 구조를 고려하여 의미 있는 단위로 분할합니다.
        - 헤더, 문단, 테이블, 이미지 블록 등을 고려
        
        Args:
            markdown_content: Markdown 내용
            
        Returns:
            청크 리스트 (각 청크는 {"text": "...", "metadata": {...}} 형태)
        """
        if not markdown_content or not markdown_content.strip():
            logger.warning("Cannot chunk empty markdown content")
            return []
        
        # Markdown을 구조 단위로 분할
        sections = self._split_into_sections(markdown_content)
        
        # 각 섹션을 청크로 변환
        chunks = []
        for section in sections:
            section_chunks = self._chunk_section(section)
            chunks.extend(section_chunks)
        
        chunks_count = len(chunks)
        logger.debug("Markdown chunking completed - chunks count: " + str(chunks_count))
        return chunks
    
    def _split_into_sections(self, markdown: str) -> List[str]:
        """
        Markdown을 섹션 단위로 분할
        
        헤더(#), 구분선(---), 테이블, 이미지 블록 등을 기준으로 분할
        
        Args:
            markdown: Markdown 내용
            
        Returns:
            섹션 리스트
        """
        sections = []
        current_section = []
        
        lines = markdown.split("\n")
        
        for line in lines:
            # 헤더나 구분선을 만나면 새 섹션 시작
            if re.match(r"^#{1,6}\s+", line) or line.strip() == "---":
                if current_section:
                    sections.append("\n".join(current_section))
                    current_section = []
            
            current_section.append(line)
        
        # 마지막 섹션 추가
        if current_section:
            sections.append("\n".join(current_section))
        
        return sections
    
    def _chunk_section(self, section: str) -> List[Dict[str, str]]:
        """
        섹션을 청크로 분할
        
        Args:
            section: 섹션 내용
            
        Returns:
            청크 리스트
        """
        if len(section) <= self.chunk_size:
            return [{"text": section.strip(), "metadata": {}}]
        
        chunks = []
        start = 0
        
        while start < len(section):
            end = start + self.chunk_size
            
            # 문장 경계에서 자르기 시도
            if end < len(section):
                # 마지막 문장 끝 찾기
                last_period = section.rfind(".", start, end)
                last_newline = section.rfind("\n", start, end)
                last_break = max(last_period, last_newline)
                
                # 문장 경계를 찾았으면 그 위치에서 자르기
                if last_break > start:
                    end = last_break + 1
            
            chunk_text = section[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "metadata": {}
                })
            
            # 다음 청크 시작 위치 (overlap 고려)
            start = end - self.chunk_overlap
            if start < 0:
                start = end
            
            # 무한 루프 방지
            if start >= len(section):
                break
        
        return chunks

