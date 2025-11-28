# 배포 전 체크리스트

## 잠재적 문제점 및 해결 방안

### 1. 파일 업로드 관련
- ✅ **파일 포인터 리셋**: `upload_file_from_request`에서 파일 포인터를 처음으로 리셋하도록 수정
- ✅ **파일 크기 제한**: `max_file_size_mb` 설정으로 제한
- ✅ **경로 조작 방지**: `sanitize_filename` 및 `Path.resolve()` 사용

### 2. 초기화 관련
- ✅ **디렉토리 생성**: `lifespan`에서 업로드/모델 캐시 디렉토리 자동 생성
- ✅ **Qdrant 초기화**: 에러 발생 시 앱 시작 실패 (의도된 동작)
- ✅ **싱글톤 패턴**: Thread-safe 싱글톤 구현

### 3. 설정 검증
- ✅ **Pydantic 검증**: `chunk_size`, `chunk_overlap`, `port`, `max_file_size_mb` 범위 검증
- ✅ **관계 검증**: `chunk_overlap < chunk_size` 검증

### 4. 리소스 관리
- ✅ **임시 파일 정리**: `finally` 블록에서 파일 정리
- ✅ **PDF 파일 핸들**: `try-finally`로 `pdf.close()` 보장

### 5. 예외 처리
- ✅ **구체적 예외**: `ValueError`, `FileNotFoundError` 등 구체적 예외 사용
- ✅ **에러 메시지**: 사용자에게는 일반적인 메시지, 로그에는 상세 정보

## 테스트 실행 방법

### 개발 의존성 설치
```bash
pip install -r requirements-dev.txt
```

### 전체 테스트 실행
```bash
pytest tests/ -v
```

### 단위 테스트만 실행
```bash
pytest tests/unit/ -v
```

### 통합 테스트만 실행
```bash
pytest tests/integration/ -v
```

### 커버리지 포함 실행 (pytest-cov 설치 필요)
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## 배포 전 확인 사항

1. ✅ 환경 변수 설정 (`.env` 파일 또는 환경 변수)
2. ✅ 디렉토리 권한 확인 (uploads, qdrant_db, models_cache)
3. ✅ 디스크 공간 확인 (모델 다운로드, 파일 업로드)
4. ✅ 포트 사용 가능 여부 확인
5. ✅ 의존성 설치 확인 (`pip install -r requirements.txt`)
6. ✅ 테스트 통과 확인 (`pytest tests/`)

## 알려진 제한사항

- 모델 다운로드: 첫 실행 시 HuggingFace에서 모델 다운로드 (시간 소요)
- 메모리 사용량: LLM 모델 로딩 시 상당한 메모리 필요
- 파일 크기: 기본 최대 100MB (설정으로 변경 가능)

