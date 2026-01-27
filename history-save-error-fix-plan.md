# HistoryService 저장/삭제 에러 해결 계획

## 문제 요약

| 문제 | 영향 | 심각도 |
|------|------|--------|
| `WinError 32` - 파일 잠금 시 삭제 실패 | 테스트 간헐적 실패, 히스토리 삭제 불가 | 높음 |
| `shutil.rmtree` 테스트 정리 실패 | CI/CD 불안정, 임시 파일 누적 | 중간 |
| 파일 쓰기 후 즉시 접근 시 충돌 | 저장 직후 로드/삭제 실패 가능 | 중간 |

**원인**: Windows 환경에서 백신, Search Indexer, GC 지연으로 인한 파일 핸들 미해제

---

## 해결 전략: 2개 PR 분리

### PR #1: 기능 수정 (Retry 메커니즘 추가)
**목적**: 파일 삭제 실패 시 재시도로 안정성 확보

### PR #2: 리팩터링 (테스트 Fixture 개선)
**목적**: pytest 기본 `tmp_path` 사용으로 정리 위임

---

## PR #1 상세 계획 (Retry 메커니즘)

### 체크리스트

- [ ] `safe_unlink()` 유틸리티 함수 추가 (재시도 로직 포함)
- [ ] `history_service.py`의 `delete_history`에서 `safe_unlink` 사용
- [ ] `file_store.py`에 `safe_rmtree()` 유틸리티 추가
- [ ] 재시도 횟수/간격 설정 가능하도록 구현

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/genesis_ai/utils/file_store.py` | `safe_unlink()`, `safe_rmtree()` 함수 추가 |
| `src/genesis_ai/services/history_service.py` | `delete_history`에서 `safe_unlink` 사용 |

### 코드 변경 예시

```python
# utils/file_store.py
import time
from pathlib import Path

def safe_unlink(path: Path, retries: int = 3, delay: float = 0.1) -> bool:
    """Windows 파일 잠금 대응 안전 삭제"""
    for attempt in range(retries):
        try:
            path.unlink()
            return True
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))  # 점진적 대기
            else:
                raise
    return False

def safe_rmtree(path: Path, retries: int = 3, delay: float = 0.1) -> bool:
    """Windows 파일 잠금 대응 안전 디렉토리 삭제"""
    import shutil
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            if attempt < retries - 1:
                time.sleep(delay * (attempt + 1))
            else:
                # 최종 시도: ignore_errors로 가능한 것만 삭제
                shutil.rmtree(path, ignore_errors=True)
                return False
    return False
```

```python
# services/history_service.py
from ..utils.file_store import safe_unlink

def delete_history(self, history_id: str) -> bool:
    try:
        meta_dir = ensure_output_dir(self._base_dir) / "metadata"
        file_path = meta_dir / f"{history_id}.json"

        if file_path.exists():
            return safe_unlink(file_path)  # 변경점
        return False
    except Exception as e:
        logger.error(f"히스토리 삭제 실패 ({history_id}): {e}")
        return False
```

---

## PR #2 상세 계획 (테스트 Fixture 개선)

### 체크리스트

- [ ] `temp_base_dir` fixture를 pytest 기본 `tmp_path` 사용으로 변경
- [ ] `safe_rmtree` 사용으로 정리 로직 강화
- [ ] 테스트 격리성 향상

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `tests/unit/test_history_service.py` | fixture 개선 |
| `tests/conftest.py` (선택) | 공통 fixture 추출 |

### 코드 변경 예시

```python
# tests/unit/test_history_service.py
import pytest
from pathlib import Path

@pytest.fixture
def temp_base_dir(tmp_path):
    """pytest 관리 임시 디렉토리 사용"""
    test_dir = tmp_path / "history_test"
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # pytest가 tmp_path 정리를 관리하므로 명시적 rmtree 불필요
```

### 대안: 기존 방식 유지 + safe_rmtree

```python
@pytest.fixture
def temp_base_dir():
    from genesis_ai.utils.file_store import safe_rmtree

    base_root = Path.cwd() / "outputs" / "pytest_tmp"
    base_root.mkdir(parents=True, exist_ok=True)
    temp_name = datetime.now().strftime("tmp_%Y%m%d_%H%M%S_%f")
    temp_dir = base_root / temp_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    safe_rmtree(temp_dir)  # 재시도 로직 적용
```

---

## 테스트 보강 포인트

### Unit Tests

| 테스트 케이스 | 파일 |
|--------------|------|
| `safe_unlink` 재시도 동작 검증 | `tests/unit/utils/test_file_store.py` |
| `PermissionError` 발생 시 재시도 확인 | 상동 |
| 최대 재시도 후 예외 발생 확인 | 상동 |
| `safe_rmtree` 부분 삭제 검증 | 상동 |

### 테스트 코드 예시

```python
# tests/unit/utils/test_file_store.py
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from genesis_ai.utils.file_store import safe_unlink

def test_safe_unlink_success(tmp_path):
    """정상 삭제 테스트"""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")

    assert safe_unlink(test_file) is True
    assert not test_file.exists()

def test_safe_unlink_retry_on_permission_error(tmp_path):
    """PermissionError 시 재시도 테스트"""
    test_file = tmp_path / "locked.txt"
    test_file.write_text("test")

    call_count = 0
    original_unlink = Path.unlink

    def mock_unlink(self):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise PermissionError("File locked")
        original_unlink(self)

    with patch.object(Path, 'unlink', mock_unlink):
        result = safe_unlink(test_file, retries=3, delay=0.01)

    assert result is True
    assert call_count == 3

def test_safe_unlink_max_retries_exceeded(tmp_path):
    """최대 재시도 초과 시 예외 발생"""
    test_file = tmp_path / "always_locked.txt"
    test_file.write_text("test")

    with patch.object(Path, 'unlink', side_effect=PermissionError("Always locked")):
        with pytest.raises(PermissionError):
            safe_unlink(test_file, retries=3, delay=0.01)
```

---

## 검증 방법

1. **Unit 테스트 실행**
   ```bash
   pytest tests/unit/utils/test_file_store.py -v
   pytest tests/unit/test_history_service.py -v
   ```

2. **병렬 테스트 실행** (문제 재현 환경)
   ```bash
   pytest tests/unit/test_history_service.py -n 4 --count=10
   ```

3. **수동 검증**
   - Windows에서 파일 생성 직후 삭제 시도
   - 백신 실시간 검사 활성화 상태에서 테스트

---

## 우선순위 권장

1. **PR #1 먼저** - 프로덕션 코드 안정성 확보 (delete_history)
2. **PR #2 이후** - 테스트 안정성 개선

## 예상 변경 규모

| PR | 파일 수 | LOC 변경 |
|----|--------|----------|
| #1 | 2 | ~40 |
| #2 | 1-2 | ~15 |

---

## 추가 고려사항

### Atomic Write (선택적 장기 개선)

```python
# file_store.py - save_metadata 개선
import tempfile
import os

def save_metadata(payload: dict, base_dir: Optional[Path] = None) -> str:
    out_dir = ensure_output_dir(base_dir) / "metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    name = datetime.now().strftime("meta_%Y%m%d_%H%M%S") + ".json"
    final_path = out_dir / name

    # 임시 파일에 먼저 쓴 후 atomic replace
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=out_dir,
        suffix='.tmp',
        delete=False,
        encoding='utf-8'
    ) as tmp:
        json.dump(payload, tmp, ensure_ascii=False, indent=2)
        tmp_path = tmp.name

    os.replace(tmp_path, final_path)  # Atomic on most OS
    return str(final_path)
```

이 개선은 PR #1, #2와 별도로 진행 가능합니다.
