# 프로젝트 구조 개선 설계서

## 1. 문제 재정의

Gemini 분석 결과에서 도출된 3가지 개선 과제:

| 과제 | 현황 | 영향도 |
|------|------|--------|
| api 디렉토리 모호성 | REST API가 아닌 유틸리티 함수 모음 | 중간 |
| README.md 미현행화 | utils, api 설명 누락 | 낮음 |
| 통합 테스트 부재 | integration/ 폴더 비어있음 | 높음 |

---

## 2. 현재 구조 요약

### 2.1 api 디렉토리 (`src/genesis_ai/api/`)

**파일**: `__init__.py` 1개

**실제 역할**:
- `retry_with_backoff()`: 지수 백오프 재시도
- `validate_json_output()`: LLM 출력 JSON 검증
- `get_hook_types()`, `generate_hook_texts()`: 마케팅 훅 생성
- `get_prompt_example()`: Veo 프롬프트 예시
- `VeoPromptEngine`: 프롬프트 엔진 re-export

**사용처**: `comment_analysis_service.py`에서 `validate_json_output` import

### 2.2 utils 디렉토리 (`src/genesis_ai/utils/`)

**파일 6개**:
| 모듈 | 역할 | 사용 빈도 |
|------|------|----------|
| logger.py | 컬러 로깅, 단축 함수 15개 | 35개 파일 |
| cache.py | TTL 캐시, @cached 데코레이터 | 5개 클라이언트 |
| error_handler.py | 예외→한국어 메시지, @safe_action | 8개 탭 |
| file_store.py | 로컬 파일 저장 | 서비스 레이어 |
| gcs_store.py | GCS 헬퍼 함수 | 스토리지 레이어 |

### 2.3 테스트 구조 (`tests/`)

```
tests/
├── conftest.py          # 공통 픽스처
├── test_smoke.py        # 스모크 테스트
├── unit/                # 11개 테스트 파일 (958줄)
│   ├── test_models.py
│   ├── test_pipeline_service.py
│   └── ... (9개 더)
└── integration/         # 비어있음 (!)
    └── __init__.py
```

---

## 3. 해결안 제시

### 해결안 A: 최소 변경 (권장)

**원칙**: 기존 코드 수정 최소화, 문서화 우선

#### 3.1 api 디렉토리 정리

**변경하지 않는 것**:
- 디렉토리 이름 변경 ❌ (import 경로 변경 필요)
- 파일 구조 변경 ❌

**변경하는 것**:
- `api/__init__.py` 상단에 docstring 추가로 역할 명확화

```python
"""
API Helpers 모듈

이 모듈은 REST API가 아닌, 서비스 레이어에서 사용하는
공통 유틸리티 함수를 제공합니다.

주요 기능:
- retry_with_backoff: API 호출 재시도 래퍼
- validate_json_output: LLM 응답 JSON 검증
- generate_hook_texts: 마케팅 훅 텍스트 생성
"""
```

#### 3.2 README.md 현행화

**수정 대상**: `gemini/README.md`

**추가 내용**:
```markdown
### 프로젝트 구조 (추가 섹션)

| 디렉토리 | 설명 |
|----------|------|
| `utils/` | 로깅, 캐싱, 에러 처리 등 횡단 관심사 |
| `api/`   | 서비스용 헬퍼 함수 (JSON 검증, 재시도 등) |
```

#### 3.3 통합 테스트 보강

**추가할 테스트 파일**:

| 파일명 | 검증 대상 | 우선순위 |
|--------|----------|----------|
| `test_pipeline_integration.py` | 전체 파이프라인 흐름 | P0 |
| `test_youtube_integration.py` | YouTube API 연동 | P1 |
| `test_gemini_integration.py` | Gemini API 연동 | P1 |

**테스트 전략**:
- 실제 API 호출 대신 녹화된 응답(VCR/responses) 사용
- 환경 변수로 실제 API 테스트 선택적 실행
- 스모크 테스트 수준으로 시작

---

### 해결안 B: 구조 개선 (선택적)

**주의**: 이 방안은 import 경로 변경이 필요하여 영향 범위가 넓음

#### api → helpers 이름 변경

**변경 범위**:
- `src/genesis_ai/api/` → `src/genesis_ai/helpers/`
- `comment_analysis_service.py` import 수정

**장점**: 이름이 역할을 정확히 반영
**단점**: 기존 코드 수정 필요, 테스트 필요

---

## 4. 추천안

### 해결안 A (최소 변경) 권장

**이유**:
1. 기존 동작 코드 수정 없음
2. 문서화만으로 혼란 해소 가능
3. 테스트 보강이 실질적 품질 향상에 기여
4. RULES.md 원칙 준수: "작게 고친다"

---

## 5. 변경 범위

### 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `src/genesis_ai/api/__init__.py` | docstring 추가 |
| `README.md` | 구조 설명 섹션 추가 |
| `tests/integration/test_pipeline_integration.py` | 신규 생성 |
| `tests/integration/test_youtube_integration.py` | 신규 생성 (P1) |
| `tests/integration/test_gemini_integration.py` | 신규 생성 (P1) |

### 수정하지 않는 파일

- `src/genesis_ai/api/` 디렉토리 구조
- `src/genesis_ai/utils/` 모든 파일
- 기존 서비스 코드 import 경로
- 기존 unit 테스트

---

## 6. 리스크

| 리스크 | 확률 | 대응 |
|--------|------|------|
| 통합 테스트가 실제 API 호출 | 중간 | 환경 변수 분기 처리 |
| README 수정 시 기존 내용 훼손 | 낮음 | 추가만 진행, 수정 최소화 |

---

## 7. 구현용 체크리스트

### Phase 1: 문서화 (즉시)
- [ ] `api/__init__.py`에 모듈 docstring 추가
- [ ] `README.md`에 utils, api 설명 추가

### Phase 2: 통합 테스트 (우선순위 P0)
- [ ] `tests/integration/test_pipeline_integration.py` 작성
  - 전체 파이프라인 실행 검증
  - Mock 서비스 사용

### Phase 3: API 통합 테스트 (우선순위 P1)
- [ ] `tests/integration/test_youtube_integration.py` 작성
- [ ] `tests/integration/test_gemini_integration.py` 작성
- [ ] 테스트용 응답 녹화 설정 (pytest-recording 또는 responses)

---

## 8. 검증 방법

```bash
# 기존 테스트 통과 확인
pytest tests/unit -v

# 통합 테스트 실행
pytest tests/integration -v

# 전체 테스트 + 커버리지
pytest --cov=src/genesis_ai
```

---

*작성일: 2026-01-28*
*작성자: Claude (설계 에이전트)*
