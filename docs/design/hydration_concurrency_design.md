# FeatureHydrator 동시성 제한 설계 문서

**작성일:** 2026-01-27
**기반 문서:** `gemini/docs/triage/too_many_file_descriptors.md`
**역할:** 설계 및 리팩터링 계획 (구현 제외)

---

## 1. 문제 재정의

### 1.1 현상
- **에러 메시지:** `ValueError: too many file descriptors in select()`
- **발생 시점:** X-Algorithm Feature Hydration 단계
- **결과:** 파이프라인 실행 중단, 분석 실패

### 1.2 원인
- Windows `SelectorEventLoop`의 파일 디스크립터 제한: **512개**
- `FeatureHydrator.hydrate()` 메서드에서 동시성 제어 없이 모든 API 호출 동시 실행
- 수백 개 댓글 처리 시 512개 제한 초과

### 1.3 영향
- 대량 댓글 처리 시 크래시
- X-Algorithm 파이프라인 불안정

---

## 2. 현재 구조 요약

### 2.1 호출 흐름

```
PipelineService.execute() (pipeline_service.py:136-138)
    │
    └─→ _run_async(self._orchestrator.run_pipeline(comments))
         │
         └─→ Orchestrator.run_pipeline() (orchestrator.py:55)
              │
              └─→ self.hydrator.hydrate(candidates)
                   │
                   └─→ FeatureHydrator.hydrate() (hydration.py:18-31)
                        │
                        ├─→ tasks = [_analyze_single_comment(c) for c in candidates]
                        │
                        └─→ asyncio.gather(*tasks)  ← 무제한 동시 실행 ❌
                             │
                             └─→ N개 Gemini API 동시 호출
                                  │
                                  └─→ N > 512 → 크래시
```

### 2.2 문제 코드

**파일:** `src/genesis_ai/services/pipeline/stages/hydration.py`
**라인:** 18-31

```python
async def hydrate(self, candidates: List[Candidate]) -> List[Candidate]:
    """
    Gemini를 통해 댓글들의 Feature를 추출하고 채워넣음
    """
    if not candidates:
        return []

    tasks = [self._analyze_single_comment(c) for c in candidates]
    results = await asyncio.gather(*tasks)  # 라인 29: 무제한 동시 실행

    return results
```

### 2.3 프로젝트 내 Semaphore 사용 현황
- **없음** - 프로젝트 전체에서 Semaphore 미사용

---

## 3. 해결안 제시

### 해결안 A: Semaphore 도입 (추천)

**대상 파일:** `src/genesis_ai/services/pipeline/stages/hydration.py`

**접근 방식:**
1. 클래스 상수로 `MAX_CONCURRENT = 10` 정의
2. `__init__`에서 `asyncio.Semaphore` 초기화
3. `_analyze_with_semaphore` 래퍼 메서드 추가
4. `hydrate` 메서드에서 래퍼 사용

**구현 스케치:**

```python
import asyncio
from typing import List

from genesis_ai.core.interfaces import IMarketingAIService
from genesis_ai.services.pipeline.types import Candidate, CandidateFeatures
from genesis_ai.utils.logger import log_error


class FeatureHydrator:
    """
    X-Algorithm의 Feature Hydration 단계
    각 댓글(Candidate)에 대해 LLM을 사용해 Feature를 추출
    """

    MAX_CONCURRENT = 10  # 동시 실행 제한

    def __init__(self, gemini_client: IMarketingAIService):
        self.gemini_client = gemini_client
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

    async def hydrate(self, candidates: List[Candidate]) -> List[Candidate]:
        """
        Gemini를 통해 댓글들의 Feature를 추출하고 채워넣음
        Semaphore로 동시성 제한 (Windows 파일 디스크립터 제한 대응)
        """
        if not candidates:
            return []

        tasks = [self._analyze_with_semaphore(c) for c in candidates]
        results = await asyncio.gather(*tasks)

        return results

    async def _analyze_with_semaphore(self, candidate: Candidate) -> Candidate:
        """Semaphore로 동시성 제한"""
        async with self._semaphore:
            return await self._analyze_single_comment(candidate)

    async def _analyze_single_comment(self, candidate: Candidate) -> Candidate:
        # 기존 코드 유지 (라인 33-77)
        ...
```

---

### 해결안 B: 배치 처리 (대안)

**접근 방식:**
1. candidates를 BATCH_SIZE 단위로 분할
2. 각 배치를 순차 처리

**구현 스케치:**

```python
async def hydrate(self, candidates: List[Candidate]) -> List[Candidate]:
    if not candidates:
        return []

    BATCH_SIZE = 10
    results = []

    for i in range(0, len(candidates), BATCH_SIZE):
        batch = candidates[i:i + BATCH_SIZE]
        tasks = [self._analyze_single_comment(c) for c in batch]
        batch_results = await asyncio.gather(*tasks)
        results.extend(batch_results)

    return results
```

**단점:**
- 배치 간 대기 시간 발생
- Semaphore보다 유연성 낮음

---

## 4. 추천안 선택

| 항목 | 내용 |
|------|------|
| 추천안 | 해결안 A (Semaphore 도입) |
| 이유 | 유연한 동시성 제어, Python 표준 패턴, 코드 변경 최소화 |

---

## 5. 변경 범위

### 수정 대상 파일

| 파일 경로 | 변경 내용 | 라인 | 우선순위 |
|-----------|----------|------|---------|
| `src/genesis_ai/services/pipeline/stages/hydration.py` | Semaphore 도입 | 전체 | **P0** |

### 수정하지 않는 파일

| 파일 경로 | 이유 |
|-----------|------|
| `orchestrator.py` | 호출부만, 내부 변경 불필요 |
| `gemini_client.py` | API 클라이언트 유지 |
| `pipeline_service.py` | 변경 불필요 |
| `filter.py` | 무관 |
| `types.py` | 데이터 구조 변경 없음 |

---

## 6. 리스크

| 리스크 | 영향도 | 발생 확률 | 완화 전략 |
|--------|--------|-----------|-----------|
| 처리 속도 저하 | 중 | 높음 | MAX_CONCURRENT 값 조정 (10~50) |
| 기존 테스트 영향 | 낮음 | 낮음 | 기능 변경 없음, 동작 동일 |
| Semaphore 초기화 시점 | 낮음 | 중간 | `__init__`에서 초기화 |

---

## 7. 구현용 체크리스트

### Phase 1: Semaphore 도입

- [ ] `hydration.py` 열기
- [ ] 클래스 상단에 `MAX_CONCURRENT = 10` 상수 추가
- [ ] `__init__` 메서드에 `self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)` 추가
- [ ] `_analyze_with_semaphore` 래퍼 메서드 추가:
  ```python
  async def _analyze_with_semaphore(self, candidate: Candidate) -> Candidate:
      async with self._semaphore:
          return await self._analyze_single_comment(candidate)
  ```
- [ ] `hydrate` 메서드의 tasks 생성 부분 수정:
  ```python
  tasks = [self._analyze_with_semaphore(c) for c in candidates]
  ```

### Phase 2: 검증

- [ ] 100개 이상 댓글로 X-Algorithm 실행
- [ ] `too many file descriptors` 에러 없이 완료 확인
- [ ] 인사이트 정상 생성 확인

---

## 8. 검증 방법

1. **에러 재현 방지 확인:**
   - 대량 댓글 (100개 이상) 처리 테스트
   - `ValueError: too many file descriptors` 에러 발생하지 않음 확인

2. **기능 정상 동작:**
   - X-Algorithm 인사이트 정상 생성 확인
   - 처리 시간 측정 (선택적)

3. **동시성 확인 (선택적):**
   - 로그 추가하여 동시 실행 수 모니터링
   ```python
   log_info(f"Semaphore acquired: {self.MAX_CONCURRENT - self._semaphore._value}/{self.MAX_CONCURRENT}")
   ```

---

## 9. MAX_CONCURRENT 값 가이드

| 값 | 사용 환경 | 비고 |
|-----|----------|------|
| 10 | 안전 기본값 | 권장 |
| 20-30 | 일반 사용 | Windows 안전 범위 |
| 50 | 고성능 필요 시 | 모니터링 필요 |
| 100+ | Linux/macOS | Windows에서는 비권장 |

---

**문서 끝**
