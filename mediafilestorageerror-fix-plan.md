# MediaFileStorageError 해결 계획

## 문제 요약

| 문제 | 영향 | 심각도 |
|------|------|--------|
| 업로드 실패 시 `PipelineResult.success=True` 반환 | 사용자가 실패 인지 불가 | 높음 |
| 업로드 전 GCS 연결 검증 없음 | 파이프라인 끝에서 실패 발견 | 중간 |
| `product['name']` 특수문자 미처리 | 400 Bad Request 발생 가능 | 낮음 |

---

## 해결 전략: 2개 PR 분리

### PR #1: 리팩터링 (upload_status 필드 추가)
**목적**: `PipelineResult`에 업로드 상태 세분화

### PR #2: 기능 수정 (Fail-Fast + 파일명 정규화)
**목적**: 조기 검증 및 안전한 경로 생성

---

## PR #1 상세 계획 (리팩터링)

### 체크리스트

- [ ] `PipelineResult`에 `upload_status` 필드 추가
- [ ] `UploadStatus` Enum 정의 (`success`, `partial`, `failed`, `skipped`)
- [ ] `_upload_to_gcs`가 업로드 결과 반환하도록 수정
- [ ] `execute()`에서 upload_status 설정

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/genesis_ai/core/models/pipeline.py` | `UploadStatus` Enum, `PipelineResult.upload_status` 필드 추가 |
| `src/genesis_ai/services/pipeline_service.py` | `_upload_to_gcs` 반환값 변경, `execute`에서 상태 설정 |

### 코드 변경 예시

```python
# core/models/pipeline.py
class UploadStatus(str, Enum):
    SUCCESS = "success"      # 모든 업로드 성공
    PARTIAL = "partial"      # 일부 실패
    FAILED = "failed"        # 전체 실패
    SKIPPED = "skipped"      # 업로드 미사용

class PipelineResult(BaseModel):
    # 기존 필드...
    upload_status: UploadStatus = Field(
        default=UploadStatus.SKIPPED,
        description="GCS 업로드 상태"
    )
    upload_errors: list[str] = Field(
        default_factory=list,
        description="업로드 실패 상세"
    )
```

```python
# services/pipeline_service.py
def _upload_to_gcs(...) -> tuple[UploadStatus, list[str]]:
    errors = []
    # ... 각 업로드 try-except에서 errors.append(str(e))
    if not errors:
        return UploadStatus.SUCCESS, []
    elif len(errors) < total_uploads:
        return UploadStatus.PARTIAL, errors
    else:
        return UploadStatus.FAILED, errors
```

---

## PR #2 상세 계획 (기능 수정)

### 체크리스트

- [ ] `execute()` 초기에 `storage.health_check()` 호출
- [ ] health_check 실패 시 경고 로그 + 조기 반환 옵션
- [ ] `build_gcs_prefix`에 slugify 강화 (연속 하이픈 제거 등)
- [ ] `_upload_to_gcs` 진입 전 경로 검증

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/genesis_ai/services/pipeline_service.py` | health_check 호출 추가 |
| `src/genesis_ai/utils/gcs_store.py` | `build_gcs_prefix` slugify 강화 |
| `src/genesis_ai/infrastructure/storage/gcs_storage.py` | health_check 개선 (선택) |

### 코드 변경 예시

```python
# services/pipeline_service.py - execute() 초반
if config.upload_to_gcs:
    if not self._storage.health_check():
        log_warning("GCS 연결 불가 - 업로드가 실패할 수 있습니다")
        # 옵션: config.upload_to_gcs = False로 자동 비활성화
```

```python
# utils/gcs_store.py
import re

def build_gcs_prefix(product: dict, kind: str) -> str:
    name = product.get("name", "product")
    # 강화된 slugify
    safe = re.sub(r"[^a-z0-9]+", "-", name.lower())
    safe = safe.strip("-")[:50]  # 길이 제한
    if not safe:
        safe = "unknown"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"genesis-korea/{kind}/{safe}/{ts}"
```

---

## 테스트 보강 포인트

### Unit Tests

| 테스트 케이스 | 파일 |
|--------------|------|
| `UploadStatus` 반환 검증 | `tests/unit/services/test_pipeline_service.py` |
| 부분 업로드 실패 시 `PARTIAL` 반환 | 상동 |
| `build_gcs_prefix` 특수문자 처리 | `tests/unit/utils/test_gcs_store.py` |
| 빈 product name 처리 | 상동 |

### Integration Tests

| 테스트 케이스 | 설명 |
|--------------|------|
| GCS 연결 실패 시나리오 | Mock으로 `health_check` False 반환 |
| 업로드 부분 실패 시나리오 | 특정 upload만 예외 발생 |

### 테스트 코드 예시

```python
# tests/unit/utils/test_gcs_store.py
@pytest.mark.parametrize("name,expected", [
    ("테스트 제품!", "------"),  # 한글+특수문자
    ("Product/Name\\Test", "product-name-test"),
    ("", "unknown"),
    ("A" * 100, "a" * 50),  # 길이 제한
])
def test_build_gcs_prefix_slugify(name, expected):
    result = build_gcs_prefix({"name": name}, "test")
    assert expected in result
```

---

## 검증 방법

1. **Unit 테스트 실행**
   ```bash
   pytest tests/unit/services/test_pipeline_service.py -v
   pytest tests/unit/utils/test_gcs_store.py -v
   ```

2. **통합 테스트** (Mock GCS)
   ```bash
   pytest tests/integration/ -k "gcs" -v
   ```

3. **수동 검증**
   - GCS 키 없이 파이프라인 실행 → `upload_status=FAILED` 확인
   - 특수문자 포함 제품명으로 실행 → 정상 경로 생성 확인

---

## 우선순위 권장

1. **PR #1 먼저** - 현재 silent failure 문제 해결이 급함
2. **PR #2 이후** - Fail-Fast는 UX 개선 성격

## 예상 변경 규모

| PR | 파일 수 | LOC 변경 |
|----|--------|----------|
| #1 | 2 | ~50 |
| #2 | 3 | ~30 |
