# LangChain → LangGraph 마이그레이션 계획

## 현재 상황

**현재 구현**: LangChain 없이 직접 구현 (Native Implementation)
- Qdrant Client 직접 사용
- Sentence Transformers 직접 사용
- HuggingFace Transformers 직접 사용

**목표**: LangChain 기반으로 리팩토링 → LangGraph로 고도화

## 마이그레이션 단계

### Phase 1: LangChain 기반 리팩토링

#### 1.1 의존성 추가
```txt
langchain>=0.1.0
langchain-community>=0.0.20
langchain-core>=0.1.0
langchain-qdrant>=0.1.0
langchain-huggingface>=0.0.1
```

#### 1.2 마이그레이션 대상 컴포넌트

| 현재 컴포넌트 | LangChain 대체 | 위치 |
|--------------|---------------|------|
| `VectorRepository` | `Qdrant` VectorStore | `src/repositories/vector_repository.py` |
| `EmbeddingGenerator` | `HuggingFaceEmbeddings` | `src/utils/embedding_generator.py` |
| `QwenManager` | `HuggingFacePipeline` / Custom LLM | `src/managers/qwen.py` |
| `RAGPipeline` | `RetrievalQA` Chain | `src/services/pipeline.py` |
| `RAGPromptTemplate` | LangChain Prompt Templates | `src/services/prompt.py` |

#### 1.3 리팩토링 구조

```
현재 구조:
RAGService
  └─> RAGPipeline
        ├─> VectorRepository (Qdrant 직접)
        ├─> EmbeddingGenerator (Sentence Transformers 직접)
        └─> QwenManager (HuggingFace 직접)

LangChain 구조:
RAGService
  └─> RetrievalQA Chain
        ├─> Qdrant VectorStore (LangChain)
        ├─> HuggingFaceEmbeddings (LangChain)
        └─> HuggingFacePipeline LLM (LangChain)
```

### Phase 2: LangGraph 고도화

#### 2.1 LangGraph 추가 의존성
```txt
langgraph>=0.0.20
```

#### 2.2 LangGraph 구조 설계

**현재 RAG 플로우 (Linear)**:
```
Query → Retrieve → Generate → Response
```

**LangGraph 플로우 (Graph-based)**:
```
START
  ↓
Query Router (조건부 분기)
  ├─> Simple Query → Direct Answer
  ├─> Complex Query → RAG Pipeline
  │     ├─> Retrieve
  │     ├─> Re-rank (선택적)
  │     ├─> Generate
  │     └─> Validate Answer
  └─> Multi-turn → Memory + RAG
        ↓
END
```

#### 2.3 LangGraph 노드 구성

1. **Router Node**: 쿼리 복잡도 판단
2. **Retrieve Node**: 벡터 검색
3. **Re-rank Node**: 검색 결과 재정렬 (선택적)
4. **Generate Node**: 답변 생성
5. **Validate Node**: 답변 품질 검증
6. **Memory Node**: 대화 기록 관리
7. **Fallback Node**: 오류 처리

#### 2.4 상태 관리 (State)

```python
class RAGState(TypedDict):
    query: str
    context: List[str]
    answer: str
    sources: List[Dict]
    history: List[Dict]
    metadata: Dict
```

## 구현 우선순위

### 우선순위 1: LangChain 기반 리팩토링
1. ✅ LangChain 의존성 추가
2. ✅ Qdrant VectorStore로 마이그레이션
3. ✅ HuggingFaceEmbeddings로 마이그레이션
4. ✅ HuggingFacePipeline LLM으로 마이그레이션
5. ✅ RetrievalQA Chain 구성
6. ✅ 기존 API 호환성 유지

### 우선순위 2: LangGraph 고도화
1. ✅ LangGraph 의존성 추가
2. ✅ 상태 모델 정의
3. ✅ 노드 구현
4. ✅ 그래프 구성
5. ✅ 조건부 라우팅 구현
6. ✅ 메모리 관리 추가

## 마이그레이션 전략

### 전략 1: 점진적 마이그레이션
- 기존 코드와 병행 운영
- Feature Flag로 전환
- 단계별 테스트

### 전략 2: 하이브리드 접근
- LangChain으로 핵심 기능 마이그레이션
- 커스텀 로직은 Wrapper로 유지
- 점진적으로 LangChain 기능으로 대체

## 예상 이점

### LangChain 사용 시
- ✅ 표준화된 인터페이스
- ✅ 풍부한 커뮤니티 예제
- ✅ 다양한 통합 컴포넌트
- ✅ 메모리, 체인, 에이전트 기능

### LangGraph 고도화 시
- ✅ 복잡한 워크플로우 관리
- ✅ 조건부 분기 처리
- ✅ 상태 기반 대화 관리
- ✅ 에이전트 오케스트레이션
- ✅ 시각화 및 디버깅

## 주의사항

1. **의존성 증가**: LangChain/LangGraph 추가로 의존성 증가
2. **성능**: Wrapper 레이어로 인한 약간의 오버헤드 가능
3. **학습 곡선**: LangChain/LangGraph 학습 필요
4. **호환성**: 기존 API 엔드포인트 유지 필요

## 다음 단계

1. **Phase 1 시작**: LangChain 기반 리팩토링
2. **테스트**: 기존 기능 동작 확인
3. **Phase 2 진행**: LangGraph 고도화
4. **최적화**: 성능 및 기능 개선

