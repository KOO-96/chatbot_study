# LangChain 구현 가이드

## 현재 vs LangChain 비교

### 현재 구현 예시

```python
# 현재: 직접 구현
class RAGPipeline:
    async def retrieve(self, query: str, top_k: int = 5):
        query_embedding = self.embedding_generator.generate_embedding(query)
        results = await self.vector_repository.search_similar(query, top_k)
        return results
    
    async def generate(self, query: str, contexts: List[str]):
        if self.llm_manager:
            answer = await self.llm_manager.generate_with_context(query, contexts)
        else:
            answer = self.prompt_template.build_simple_response(query, contexts)
        return answer
```

### LangChain 구현 예시

```python
# LangChain: 표준화된 인터페이스
from langchain.chains import RetrievalQA
from langchain_community.vectorstores import Qdrant
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFacePipeline

# VectorStore 초기화
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large-instruct"
)
vectorstore = Qdrant.from_existing_collection(
    client=qdrant_client,
    collection_name="rag_documents",
    embeddings=embeddings
)

# LLM 초기화
llm = HuggingFacePipeline.from_model_id(
    model_id="Qwen/Qwen3-VL-2B-Instruct",
    task="text-generation",
    device_map="cpu"
)

# RAG Chain 구성
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True
)

# 사용
result = qa_chain.invoke({"query": "사용자 질문"})
```

## LangGraph 구현 예시

### 기본 그래프 구조

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RAGState(TypedDict):
    query: str
    context: List[str]
    answer: str
    sources: List[Dict]
    history: List[Dict]

def router_node(state: RAGState) -> str:
    """쿼리 복잡도에 따라 라우팅"""
    if len(state["query"]) < 20:
        return "simple"
    return "complex"

def retrieve_node(state: RAGState) -> RAGState:
    """벡터 검색"""
    retriever = vectorstore.as_retriever()
    docs = retriever.get_relevant_documents(state["query"])
    state["context"] = [doc.page_content for doc in docs]
    state["sources"] = [{"source": doc.metadata} for doc in docs]
    return state

def generate_node(state: RAGState) -> RAGState:
    """답변 생성"""
    prompt = f"Context: {state['context']}\n\nQuestion: {state['query']}"
    state["answer"] = llm.invoke(prompt)
    return state

# 그래프 구성
workflow = StateGraph(RAGState)
workflow.add_node("router", router_node)
workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_conditional_edges("router", router_node)
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)
workflow.set_entry_point("router")

app = workflow.compile()
```

## 마이그레이션 체크리스트

- [ ] LangChain 의존성 추가
- [ ] Qdrant VectorStore로 전환
- [ ] HuggingFaceEmbeddings로 전환
- [ ] HuggingFacePipeline LLM으로 전환
- [ ] RetrievalQA Chain 구성
- [ ] 기존 API 호환성 테스트
- [ ] LangGraph 의존성 추가
- [ ] 상태 모델 정의
- [ ] 노드 구현
- [ ] 그래프 구성
- [ ] 조건부 라우팅 구현
- [ ] 메모리 관리 추가

