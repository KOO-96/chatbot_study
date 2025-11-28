"""
프롬프트 템플릿 관리

RAG 및 기타 서비스에서 사용할 프롬프트 템플릿을 관리합니다.
"""
from typing import List, Optional


class PromptTemplate:
    """프롬프트 템플릿 기본 클래스"""
    
    @staticmethod
    def format(template: str, **kwargs) -> str:
        """
        프롬프트 템플릿 포맷팅
        
        Args:
            template: 템플릿 문자열
            **kwargs: 템플릿 변수
            
        Returns:
            포맷팅된 프롬프트
        """
        return template.format(**kwargs)


class RAGPromptTemplate:
    """RAG 질의 응답용 프롬프트 템플릿"""
    
    # 기본 시스템 프롬프트
    SYSTEM_PROMPT = """당신은 주어진 문서만을 기반으로 답변하는 AI 어시스턴트입니다.

절대적인 규칙 (반드시 지켜야 함):
1. **문서에 나온 내용만 그대로 사용하세요.** 문서에 없는 설명, 해석, 추론을 추가하지 마세요.
2. **문서에 나온 항목, 구성 요소를 나열하거나 인용하세요.** 각 항목에 대한 추가 설명을 만들지 마세요.
3. **표 형식 데이터에서 항목 이름과 설명을 그대로 사용하세요.** 새로운 해석이나 설명을 만들지 마세요.
4. **질문과 관련된 내용이 문서에 있으면 문서에 나온 항목들을 나열하여 답변하세요.**
5. **문서 내용과 질문이 정말 관련이 없을 때만 "제공된 문서에서 해당 질문에 대한 정보를 찾을 수 없습니다."라고 답변하세요.**
6. **추측, 일반 지식, 외부 정보를 절대 사용하지 마세요.** 문서에 없는 내용을 만들어내거나 추론하지 마세요.
7. **답변은 간결하게 작성하세요.** (최대 300자 이내)
8. **같은 내용을 반복하지 마세요.**
9. **문서에 나온 용어와 개념을 정확히 그대로 사용하세요.**"""
    
    # 기본 질의 응답 프롬프트
    QUERY_PROMPT = """{system_prompt}

=== 참고 문서 내용 (이 내용만 사용하세요) ===
{contexts}
==========================================

사용자 질문: {query}

**중요 지시사항**:
1. 위 문서 내용을 **꼼꼼히 읽고 분석**하세요. 표 형식 데이터도 포함됩니다.
2. 문서에 나온 **항목 이름과 설명을 그대로 사용**하세요. 새로운 설명을 만들지 마세요.
3. 질문과 관련된 내용이 문서에 있으면 **문서에 나온 항목들을 나열**하여 답변하세요.
4. 각 항목에 대한 추가 설명이나 해석을 만들지 마세요. 문서에 나온 내용만 사용하세요.
5. 문서에 관련 정보가 **정말 없을 때만** "제공된 문서에서 해당 질문에 대한 정보를 찾을 수 없습니다."라고 답변하세요.
6. 답변은 간결하게 작성하세요 (최대 300자).

답변:"""
    
    # 간단한 응답 생성용 프롬프트 (LLM 없이 사용) - 개선됨
    SIMPLE_RESPONSE_PROMPT = """질문: {query}

제공된 문서에서 찾은 관련 정보:

{contexts}

참고: 위 정보는 제공된 문서에서 추출한 내용입니다. 더 정확한 답변을 원하시면 LLM을 사용하는 옵션을 활성화해주세요."""
    
    @classmethod
    def get_system_prompt(cls, custom_prompt: Optional[str] = None) -> str:
        """
        시스템 프롬프트 가져오기
        
        Args:
            custom_prompt: 커스텀 시스템 프롬프트 (None이면 기본값 사용)
            
        Returns:
            시스템 프롬프트
        """
        return custom_prompt or cls.SYSTEM_PROMPT
    
    @classmethod
    def build_query_prompt(
        cls,
        query: str,
        contexts: List[str],
        system_prompt: Optional[str] = None,
        max_context_length: int = 3000
    ) -> str:
        """
        질의 응답용 프롬프트 생성
        
        Args:
            query: 사용자 질문
            contexts: 관련 문서 컨텍스트 리스트
            system_prompt: 커스텀 시스템 프롬프트
            max_context_length: 최대 컨텍스트 길이
            
        Returns:
            완성된 프롬프트
        """
        # 컨텍스트 결합 및 길이 제한
        combined_context = "\n\n".join(contexts)
        if len(combined_context) > max_context_length:
            combined_context = combined_context[:max_context_length] + "..."
        
        sys_prompt = cls.get_system_prompt(system_prompt)
        
        return cls.QUERY_PROMPT.format(
            system_prompt=sys_prompt,
            contexts=combined_context,
            query=query
        )
    
    @classmethod
    def build_simple_response(
        cls,
        query: str,
        contexts: List[str],
        max_context_length: int = 1000
    ) -> str:
        """
        간단한 응답 생성용 프롬프트 (LLM 없이 사용)
        
        Args:
            query: 사용자 질문
            contexts: 관련 문서 컨텍스트 리스트
            max_context_length: 최대 컨텍스트 길이
            
        Returns:
            간단한 응답 텍스트
        """
        if not contexts:
            return "제공된 문서에서 질문과 관련된 정보를 찾을 수 없습니다."
        
        # 상위 3개 컨텍스트만 사용 (가장 관련성 높은 것)
        top_contexts = contexts[:3]
        
        # 각 컨텍스트를 정리하고 요약
        cleaned_contexts = []
        for i, ctx in enumerate(top_contexts, 1):
            # 앞뒤 공백 제거 및 줄바꿈 정리
            cleaned = ctx.strip()
            # 연속된 줄바꿈 정리
            cleaned = "\n".join(line.strip() for line in cleaned.split("\n") if line.strip())
            # 너무 긴 경우 자르기
            if len(cleaned) > max_context_length // 3:
                cleaned = cleaned[:max_context_length // 3] + "..."
            cleaned_contexts.append(f"[문서 {i}]\n{cleaned}")
        
        combined_context = "\n\n".join(cleaned_contexts)
        
        return cls.SIMPLE_RESPONSE_PROMPT.format(
            query=query,
            contexts=combined_context
        )


class DocumentProcessingPrompt:
    """문서 처리용 프롬프트 템플릿"""
    
    # 문서 요약 프롬프트
    SUMMARIZE_PROMPT = """다음 문서의 주요 내용을 요약해주세요:

{document}

요약:"""
    
    # 문서 키워드 추출 프롬프트
    EXTRACT_KEYWORDS_PROMPT = """다음 문서에서 주요 키워드를 추출해주세요:

{document}

키워드:"""
    
    @classmethod
    def build_summarize_prompt(cls, document: str) -> str:
        """
        문서 요약 프롬프트 생성
        
        Args:
            document: 문서 내용
            
        Returns:
            요약 프롬프트
        """
        return cls.SUMMARIZE_PROMPT.format(document=document)
    
    @classmethod
    def build_extract_keywords_prompt(cls, document: str) -> str:
        """
        키워드 추출 프롬프트 생성
        
        Args:
            document: 문서 내용
            
        Returns:
            키워드 추출 프롬프트
        """
        return cls.EXTRACT_KEYWORDS_PROMPT.format(document=document)

