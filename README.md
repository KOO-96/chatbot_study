# RAG System with FastAPI

FastAPI를 활용한 RAG (Retrieval-Augmented Generation) 시스템입니다. PDF와 TXT 파일을 업로드하여 벡터화하고, Qdrant 벡터 데이터베이스에 저장하여 검색 및 질의 응답을 제공합니다.

## 아키텍처

이 프로젝트는 **레이어드 아키텍처(Layered Architecture)**를 따르며, 비즈니스 로직을 명확하게 분리합니다:

- **Models**: 데이터 모델 (Document, Chunk, SearchResult 등)
- **DTOs**: 요청/응답 데이터 전송 객체
- **Controllers**: API 엔드포인트 및 요청 처리
- **Services**: 비즈니스 로직 계층
- **Repositories**: 데이터 접근 계층 (Qdrant 연동)
- **Config**: 애플리케이션 설정

## 주요 기능

- 📄 **파일 업로드**: PDF 및 TXT 파일 업로드 지원
- 🔍 **벡터 검색**: Qdrant를 활용한 의미 기반 검색
- 💬 **RAG 질의 응답**: 업로드된 문서를 기반으로 한 질의 응답
- 🗄️ **로컬 Qdrant**: 로컬 경로에서 Qdrant 벡터 DB 운영
- 🏗️ **명확한 계층 분리**: 비즈니스 로직과 데이터 접근 계층 분리

## 기술 스택

- **FastAPI**: 웹 프레임워크
- **Qdrant**: 벡터 데이터베이스 (로컬)
- **Sentence Transformers**: 텍스트 임베딩 생성
- **PyPDF2**: PDF 파일 처리
- **Pydantic**: 데이터 검증 및 모델링

## 프로젝트 구조

```
chatbot/
├── main.py                      # FastAPI 메인 애플리케이션
├── requirements.txt             # Python 의존성
├── src/
│   ├── models/                  # 데이터 모델
│   │   ├── document.py          # Document 모델
│   │   ├── chunk.py             # Chunk 모델
│   │   └── search_result.py     # SearchResult 모델
│   ├── dto/                     # 데이터 전송 객체
│   │   ├── upload_dto.py        # 업로드 요청/응답 DTO
│   │   ├── query_dto.py         # 질의 요청/응답 DTO
│   │   └── document_dto.py      # 문서 관련 DTO
│   ├── routers/                 # API 라우터
│   │   ├── document_router.py  # 문서 관리 엔드포인트
│   │   └── chat_router.py       # 채팅/질의 응답 엔드포인트
│   ├── services/                # 비즈니스 로직 계층
│   │   ├── file_service.py      # 파일 처리 서비스
│   │   ├── document_service.py  # 문서 관리 서비스
│   │   └── rag_service.py       # RAG 질의 응답 서비스
│   ├── repositories/           # 데이터 접근 계층
│   │   └── vector_repository.py # Qdrant 벡터 리포지토리
│   └── core/                    # 핵심 설정 및 유틸리티
│       └── config.py            # 애플리케이션 설정
├── uploads/                     # 업로드된 파일 임시 저장 (자동 삭제)
├── qdrant_db/                   # Qdrant 로컬 데이터베이스
└── README.md
```

## 설치 방법

1. **의존성 설치**

```bash
pip install -r requirements.txt
```

**주의**: `pydantic-settings` 패키지가 설치되지 않은 경우 다음 명령어로 설치하세요:
```bash
pip install pydantic-settings==2.1.0
```

2. **애플리케이션 실행**

```bash
uvicorn main:app --reload
```

또는

```bash
python main.py
```

서버는 `http://localhost:8000`에서 실행됩니다.

## API 엔드포인트

### 1. 파일 업로드

**POST** `/api/v1/document`

PDF 또는 TXT 파일을 업로드하여 벡터화합니다.

```bash
curl -X POST "http://localhost:8000/api/v1/document" \
  -F "file=@example.pdf"
```

**응답 예시:**
```json
{
  "message": "파일 업로드 및 벡터화 완료",
  "filename": "example.pdf",
  "chunks_count": 15,
  "document_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 2. 질의 응답 (Chat)

**POST** `/api/v1/chat`

업로드된 문서를 기반으로 질의 응답을 제공합니다.

```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "문서의 주요 내용은 무엇인가요?", "top_k": 5}'
```

### 3. 질의 응답 (디버깅용)

**POST** `/api/v1/chat/document`

질문하면 어떤 문서를 검색하는지 확인하는 디버깅용 엔드포인트입니다.

```bash
curl -X POST "http://localhost:8000/api/v1/chat/document" \
  -H "Content-Type: application/json" \
  -d '{"query": "문서의 주요 내용은 무엇인가요?", "top_k": 5}'
```

**응답 예시:**
```json
{
  "query": "문서의 주요 내용은 무엇인가요?",
  "answer": "질문: 문서의 주요 내용은 무엇인가요?\n\n관련 문서에서 찾은 정보:\n\n...",
  "contexts": ["관련 텍스트 청크 1", "관련 텍스트 청크 2"],
  "sources": [
    {
      "text": "관련 텍스트...",
      "score": 0.85,
      "metadata": {
        "document_id": "uuid-here",
        "chunk_index": 0,
        "filename": "example.pdf",
        "file_type": "pdf"
      }
    }
  ],
  "top_k": 5
}
```

### 4. 문서 목록 조회

**GET** `/api/v1/document/info`

저장된 문서 목록을 조회합니다.

```bash
curl -X GET "http://localhost:8000/api/v1/document/info"
```

### 5. 문서 삭제

**DELETE** `/api/v1/document/{document_id}`

특정 문서를 삭제합니다.

```bash
curl -X DELETE "http://localhost:8000/api/v1/document/{document_id}"
```

### 6. 헬스 체크

**GET** `/health`

서비스 상태를 확인합니다.

```bash
curl -X GET "http://localhost:8000/health"
```

## 설정

### 환경 변수 설정

`.env` 파일을 생성하여 설정을 변경할 수 있습니다:

```env
# Qdrant 설정
QDRANT_COLLECTION_NAME=rag_documents
QDRANT_PATH=./qdrant_db

# 임베딩 모델 설정
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2

# 파일 처리 설정
CHUNK_SIZE=500
CHUNK_OVERLAP=50
UPLOAD_DIR=uploads

# 서버 설정
HOST=0.0.0.0
PORT=8000
```

### 코드에서 설정 변경

`src/core/config.py`에서 기본값을 변경할 수 있습니다.

## 아키텍처 설명

### 레이어드 아키텍처

1. **Controller Layer**: HTTP 요청/응답 처리
   - 요청 검증
   - DTO 변환
   - 서비스 호출

2. **Service Layer**: 비즈니스 로직
   - 파일 처리
   - 문서 관리
   - RAG 질의 응답

3. **Repository Layer**: 데이터 접근
   - Qdrant 연동
   - 벡터 저장/검색
   - 데이터 변환

4. **Model Layer**: 도메인 모델
   - Document, Chunk, SearchResult 등

5. **DTO Layer**: API 계약
   - 요청/응답 스키마 정의

## 주의사항

- 현재 RAG 서비스는 간단한 컨텍스트 결합 방식으로 답변을 생성합니다. 실제 프로덕션 환경에서는 LLM (OpenAI, Anthropic 등)을 통합하여 더 나은 답변을 생성하는 것을 권장합니다.
- 첫 실행 시 임베딩 모델 다운로드로 인해 시간이 걸릴 수 있습니다.
- Qdrant 데이터베이스는 `qdrant_db/` 디렉토리에 로컬로 저장됩니다.

## API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 개발 가이드

### 새로운 기능 추가 시

1. **Model 정의**: `src/models/`에 도메인 모델 추가
2. **DTO 정의**: `src/dto/`에 요청/응답 DTO 추가
3. **Repository 구현**: `src/repositories/`에 데이터 접근 로직 추가
4. **Service 구현**: `src/services/`에 비즈니스 로직 추가 (직관적인 로직 흐름 작성)
5. **Router 구현**: `src/routers/`에 API 엔드포인트 추가
6. **Router 등록**: `main.py`에 라우터 등록

이러한 계층 분리를 통해 코드의 유지보수성과 테스트 가능성을 향상시킬 수 있습니다.
