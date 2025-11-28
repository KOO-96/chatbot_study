# 테스트 가이드

## 테스트 구조

```
tests/
├── conftest.py              # 공통 fixtures
├── test_settings.py         # 설정 검증 테스트
├── unit/                    # 단위 테스트
│   ├── test_file_utils.py  # 파일 유틸리티 테스트
│   ├── test_chunker.py     # 청커 테스트
│   └── test_helper.py      # 헬퍼 유틸리티 테스트
└── integration/            # 통합 테스트
    ├── test_endpoints.py   # API 엔드포인트 테스트
    └── test_services.py   # 서비스 통합 테스트
```

## 설치

### 개발 의존성 설치
```bash
pip install -r requirements-dev.txt
```

### 프로덕션 의존성 설치
```bash
pip install -r requirements.txt
```

## 테스트 실행

### 전체 테스트 실행
```bash
pytest tests/ -v
```

### 특정 카테고리 테스트
```bash
# 단위 테스트만
pytest tests/unit/ -v

# 통합 테스트만
pytest tests/integration/ -v

# 설정 테스트만
pytest tests/test_settings.py -v
```

### 특정 테스트 파일 실행
```bash
pytest tests/unit/test_file_utils.py -v
```

### 커버리지 포함 실행 (선택사항)
```bash
pip install pytest-cov
pytest tests/ --cov=src --cov-report=term-missing
```

## 테스트 작성 가이드

### 단위 테스트
- 각 함수/메서드를 독립적으로 테스트
- Mock을 사용하여 외부 의존성 제거
- 빠르게 실행되어야 함

### 통합 테스트
- 여러 컴포넌트 간 상호작용 테스트
- 실제 파일 시스템 사용 가능
- API 엔드포인트 테스트 포함

### Fixtures 사용
- `conftest.py`에 공통 fixtures 정의
- 테스트 간 재사용 가능한 설정 제공

## 알려진 이슈

- 모델 로딩 테스트는 `@pytest.mark.slow` 마커 사용 권장
- 실제 Qdrant 연결이 필요한 테스트는 환경 변수로 제어

