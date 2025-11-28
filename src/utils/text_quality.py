"""
텍스트 품질 검증 유틸리티

답변 품질을 검증하고 개선하는 함수들을 제공합니다.
"""
import re
from typing import Optional, Tuple, List


def detect_repetition(text: str, min_repeat_length: int = 20) -> bool:
    """
    텍스트에서 반복 패턴을 감지합니다.
    
    Args:
        text: 검사할 텍스트
        min_repeat_length: 최소 반복 길이 (문자 수)
        
    Returns:
        반복이 감지되면 True, 아니면 False
    """
    if not text or len(text) < min_repeat_length * 2:
        return False
    
    # 문장 단위로 분리
    sentences = re.split(r'[.!?]\s+', text)
    
    # 연속된 유사한 문장 감지
    for i in range(len(sentences) - 1):
        if len(sentences[i]) < min_repeat_length:
            continue
        
        # 다음 문장과 유사도 확인 (간단한 방법: 공통 부분 길이)
        current = sentences[i].strip()
        next_sent = sentences[i + 1].strip()
        
        # 같은 문장이 연속으로 나타나는지 확인
        if current == next_sent:
            return True
        
        # 부분 일치 확인 (50% 이상 일치)
        if len(current) > 0 and len(next_sent) > 0:
            common_length = len(set(current.split()) & set(next_sent.split()))
            total_words = max(len(current.split()), len(next_sent.split()))
            if total_words > 0 and common_length / total_words > 0.7:
                return True
    
    # 단어 레벨 반복 감지 (같은 단어가 너무 많이 반복)
    words = text.split()
    if len(words) > 10:
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # 전체 단어의 30% 이상이 같은 단어면 반복으로 간주
        max_count = max(word_counts.values()) if word_counts else 0
        if max_count > len(words) * 0.3:
            return True
    
    return False


def clean_repetitive_text(text: str) -> str:
    """
    반복적인 텍스트를 정리합니다.
    
    Args:
        text: 정리할 텍스트
        
    Returns:
        정리된 텍스트
    """
    if not text:
        return text
    
    # 문장 단위로 분리
    sentences = re.split(r'([.!?]\s+)', text)
    
    # 유사한 문장 제거
    cleaned_sentences = []
    seen = set()
    
    for i in range(0, len(sentences), 2):  # 문장과 구분자를 함께 처리
        if i >= len(sentences):
            break
        
        sentence = sentences[i].strip()
        if not sentence:
            continue
        
        # 이미 본 문장과 유사한지 확인
        is_duplicate = False
        for seen_sent in seen:
            # 단어 레벨 유사도 확인
            current_words = set(sentence.split())
            seen_words = set(seen_sent.split())
            
            if len(current_words) > 0 and len(seen_words) > 0:
                similarity = len(current_words & seen_words) / len(current_words | seen_words)
                if similarity > 0.8:  # 80% 이상 유사하면 중복으로 간주
                    is_duplicate = True
                    break
        
        if not is_duplicate:
            cleaned_sentences.append(sentences[i])
            if i + 1 < len(sentences):
                cleaned_sentences.append(sentences[i + 1])  # 구분자 추가
            seen.add(sentence)
    
    result = ''.join(cleaned_sentences).strip()
    
    # 마지막이 잘린 경우 (끝이 "..." 또는 불완전한 문장)
    if result and not result[-1] in '.!?':
        # 마지막 문장을 완성
        last_sentence = result.split('.')[-1] if '.' in result else result
        if len(last_sentence.strip()) > 10:
            result = result.rstrip('...').rstrip()
            if result and not result[-1] in '.!?':
                result += '.'
    
    return result


def validate_answer_quality(
    answer: str, 
    min_length: int = 10, 
    max_length: int = 2000,
    contexts: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    답변 품질을 검증합니다.
    
    Args:
        answer: 검증할 답변
        min_length: 최소 길이
        max_length: 최대 길이
        contexts: 원본 컨텍스트 리스트 (문서 내용 일치도 확인용)
        
    Returns:
        (유효 여부, 오류 메시지)
    """
    if not answer or not answer.strip():
        return False, "Answer is empty"
    
    answer = answer.strip()
    
    # 길이 검증
    if len(answer) < min_length:
        return False, f"Answer is too short (minimum {min_length} characters)"
    
    if len(answer) > max_length:
        return False, f"Answer is too long (maximum {max_length} characters)"
    
    # 반복 검증
    if detect_repetition(answer):
        return False, "Answer contains repetitive content"
    
    # 문서 내용 일치도 검증 (컨텍스트가 제공된 경우)
    if contexts:
        # 답변이 문서 내용과 관련이 있는지 확인
        # 답변에 문서에 없는 단어가 많이 포함되어 있으면 문제
        answer_lower = answer.lower()
        context_text = " ".join(contexts).lower()
        
        # 답변의 주요 단어들이 컨텍스트에 있는지 확인
        answer_words = set(re.findall(r'\b\w+\b', answer_lower))
        context_words = set(re.findall(r'\b\w+\b', context_text))
        
        # 공통 단어 비율 계산 (불용어 제외)
        stopwords = {'제공', '문서', '에서', '질문', '에', '대한', '정보', '를', '을', '을', '이', '가', '는', '은', '의', '와', '과', '도', '로', '으로', '수', '있', '없', '것', '등', '및', '또는', '그리고'}
        meaningful_answer_words = answer_words - stopwords
        meaningful_context_words = context_words - stopwords
        
        if len(meaningful_answer_words) > 0:
            common_words = meaningful_answer_words & meaningful_context_words
            overlap_ratio = len(common_words) / len(meaningful_answer_words)
            
            # "문서에 없다"고 말하는 답변은 특별 처리
            # "없다", "찾을 수 없", "포함되어 있지 않" 등의 표현이 있으면 일치도 검증 완화
            negative_phrases = ['없', '찾을 수 없', '포함되어 있지 않', '설명이 없다', '정보가 없다', '관련 정보가 없다']
            has_negative_phrase = any(phrase in answer for phrase in negative_phrases)
            
            if has_negative_phrase:
                # "문서에 없다"고 말하는 경우, 일치도가 낮아도 허용 (20% 이상)
                if overlap_ratio < 0.2:
                    return False, f"Answer claims information not found but has very low context overlap (overlap: {overlap_ratio:.2f})"
            else:
                # 일반 답변은 일치도 검증 완화 (20% 이상으로 낮춤 - 작은 모델의 특성 고려)
                # 작은 모델은 문서 내용을 재구성하거나 설명을 추가할 수 있으므로 완화
                if overlap_ratio < 0.2:
                    return False, f"Answer contains too many words not found in context (overlap: {overlap_ratio:.2f})"
    
    return True, None


def post_process_answer(answer: str, max_length: int = 1000) -> str:
    """
    답변을 후처리합니다.
    
    Args:
        answer: 후처리할 답변
        max_length: 최대 길이
        
    Returns:
        후처리된 답변
    """
    if not answer:
        return answer
    
    # 반복 제거
    cleaned = clean_repetitive_text(answer)
    
    # 길이 제한
    if len(cleaned) > max_length:
        # 문장 단위로 자르기
        sentences = re.split(r'([.!?]\s+)', cleaned)
        result = []
        current_length = 0
        
        for i in range(0, len(sentences), 2):
            if i >= len(sentences):
                break
            
            sentence = sentences[i]
            if current_length + len(sentence) > max_length:
                break
            
            result.append(sentence)
            if i + 1 < len(sentences):
                result.append(sentences[i + 1])
            current_length += len(sentence)
        
        cleaned = ''.join(result).strip()
    
    return cleaned

