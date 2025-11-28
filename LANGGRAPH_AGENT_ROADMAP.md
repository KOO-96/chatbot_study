# LangGraph Agent 구현 로드맵

## 최종 목표
**LangGraph를 사용한 Agent 기반 RAG 시스템 구축**

## 현재 상태
- ✅ 기본 RAG 시스템 (Native Implementation)
- ❌ LangChain 미사용
- ❌ LangGraph 미사용
- ❌ Agent 미구현

## 구현 단계

### Phase 1: LangChain 기반 리팩토링 (1-2주)

#### 1.1 의존성 추가
```txt
langchain>=0.1.0
langchain-community>=0.0.20
langchain-core>=0.1.0
langchain-qdrant>=0.1.0
langchain-huggingface>=0.0.1
```

#### 1.2 컴포넌트 마이그레이션
- [ ] Qdrant VectorStore로 전환
- [ ] HuggingFaceEmbeddings로 전환
- [ ] HuggingFacePipeline LLM으로 전환
- [ ] RetrievalQA Chain 구성
- [ ] 기존 API 호환성 유지

### Phase 2: LangGraph 기본 구조 (1주)

#### 2.1 의존성 추가
```txt
langgraph>=0.0.20
```

#### 2.2 기본 그래프 구조
- [ ] 상태 모델 정의 (RAGState)
- [ ] 기본 노드 구현
  - Router Node (쿼리 분류)
  - Retrieve Node (벡터 검색)
  - Generate Node (답변 생성)
  - Validate Node (답변 검증)
- [ ] 간단한 선형 그래프 구성

### Phase 3: 조건부 라우팅 (1주)

#### 3.1 라우터 노드 고도화
- [ ] 쿼리 복잡도 분석
- [ ] Simple Query → Direct Answer
- [ ] Complex Query → RAG Pipeline
- [ ] Multi-turn → Memory + RAG

#### 3.2 조건부 엣지 구현
- [ ] Router → Simple/Complex 분기
- [ ] 검색 결과 품질 기반 분기
- [ ] 답변 품질 기반 재검색

### Phase 4: Agent 구현 (2-3주)

#### 4.1 Agent 구조 설계
```
Agent State:
- query: 사용자 질문
- context: 검색된 컨텍스트
- answer: 생성된 답변
- history: 대화 기록
- tools: 사용 가능한 도구
- actions: 수행한 액션
- iterations: 반복 횟수
```

#### 4.2 Agent 노드 구성
1. **Router Agent**: 쿼리 분석 및 라우팅
2. **Retrieval Agent**: 문서 검색 및 필터링
3. **Generation Agent**: 답변 생성 및 검증
4. **Reflection Agent**: 답변 품질 평가 및 개선
5. **Tool Agent**: 외부 도구 사용 (선택적)
   - 웹 검색
   - 계산기
   - 데이터베이스 쿼리

#### 4.3 Agent 워크플로우
```
START
  ↓
Router Agent (쿼리 분석)
  ├─> Simple → Direct Answer → END
  ├─> Complex → Retrieval Agent
  │     ↓
  │   Generation Agent
  │     ↓
  │   Reflection Agent (품질 검증)
  │     ├─> Good → END
  │     └─> Poor → Retrieval Agent (재검색)
  └─> Multi-turn → Memory Agent → Retrieval Agent
        ↓
      END
```

### Phase 5: 고급 기능 (1-2주)

#### 5.1 메모리 관리
- [ ] 대화 기록 저장
- [ ] 컨텍스트 윈도우 관리
- [ ] 장기 메모리 (선택적)

#### 5.2 도구 통합
- [ ] 웹 검색 도구
- [ ] 계산기 도구
- [ ] 문서 요약 도구
- [ ] 커스텀 도구

#### 5.3 모니터링 및 디버깅
- [ ] 그래프 실행 추적
- [ ] 각 노드의 입출력 로깅
- [ ] 성능 메트릭 수집

## 기술 스택

### 현재
- FastAPI
- Qdrant (직접 사용)
- Sentence Transformers (직접 사용)
- HuggingFace Transformers (직접 사용)

### 목표
- FastAPI
- LangChain
- LangGraph
- Qdrant (LangChain 통합)
- HuggingFace Embeddings (LangChain 통합)
- HuggingFace Pipeline (LangChain 통합)

## 예상 타임라인

- **Phase 1**: 1-2주 (LangChain 리팩토링)
- **Phase 2**: 1주 (LangGraph 기본 구조)
- **Phase 3**: 1주 (조건부 라우팅)
- **Phase 4**: 2-3주 (Agent 구현)
- **Phase 5**: 1-2주 (고급 기능)

**총 예상 기간**: 6-9주

## 우선순위

1. **높음**: Phase 1, 2 (기본 구조)
2. **중간**: Phase 3 (조건부 라우팅)
3. **높음**: Phase 4 (Agent - 최종 목표)
4. **낮음**: Phase 5 (고급 기능)

## 다음 단계

1. 모델 이름 수정 (Qwen2.5-4B-Instruct → 올바른 모델명)
2. Phase 1 시작: LangChain 의존성 추가 및 기본 리팩토링
3. 점진적 마이그레이션으로 기존 기능 유지

