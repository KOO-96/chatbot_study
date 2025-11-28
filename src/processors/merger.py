"""
파일 통합 모듈

여러 Markdown 파일을 하나로 통합합니다.
"""
from typing import List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class Merger:
    """파일 통합 클래스"""
    
    def __init__(self):
        """Merger 초기화"""
        pass
    
    def merge_markdown_files(self, markdown_files: List[Path], output_path: Path) -> Path:
        """
        여러 Markdown 파일을 하나로 통합
        
        Args:
            markdown_files: 통합할 Markdown 파일 경로 리스트
            output_path: 출력 파일 경로
            
        Returns:
            통합된 파일 경로
        """
        try:
            combined_content = []
            
            for md_file in markdown_files:
                if md_file.exists():
                    with open(md_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            combined_content.append(content)
            
            # 파일 간 구분선 추가
            merged_content = "\n\n---\n\n".join(combined_content)
            
            # 저장
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(merged_content)
            
            files_count = len(markdown_files)
            output_path_str = str(output_path)
            logger.debug("Markdown files merged - files count: " + str(files_count) + ", output: " + output_path_str)
            return output_path
        
        except Exception as e:
            output_path_str = str(output_path)
            logger.error("Markdown merging failed - output: " + output_path_str + ", error: " + str(e))
            raise
    
    def merge_markdown_strings(self, markdown_contents: List[str], separator: str = "\n\n---\n\n") -> str:
        """
        여러 Markdown 문자열을 하나로 통합
        
        Args:
            markdown_contents: 통합할 Markdown 내용 리스트
            separator: 구분자 (기본값: "\\n\\n---\\n\\n")
            
        Returns:
            통합된 Markdown 문자열
        """
        try:
            # 빈 내용 제거
            valid_contents = [content.strip() for content in markdown_contents if content.strip()]
            
            merged_content = separator.join(valid_contents)
            contents_count = len(valid_contents)
            logger.debug("Markdown strings merged - contents count: " + str(contents_count))
            return merged_content
        
        except Exception as e:
            logger.error("Markdown string merging failed: " + str(e))
            raise

