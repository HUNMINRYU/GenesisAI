# Hydration Concurrency Limit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** FeatureHydrator 단계의 동시성 제한을 도입해 Windows 파일 디스크립터 초과 오류를 방지한다.

**Architecture:** FeatureHydrator에 asyncio.Semaphore를 추가하고, hydrate에서 모든 작업을 세마포어 래퍼를 통해 실행한다. 기본 동작은 유지하되 동시성만 제한한다.

**Tech Stack:** Python, asyncio, pytest

---

### Task 1: FeatureHydrator에 Semaphore 적용

**Files:**
- Modify: `src/genesis_ai/services/pipeline/stages/hydration.py`
- Create: `tests/unit/test_feature_hydrator_semaphore.py`

**Step 1: Write the failing test**

```python
import asyncio

import pytest

from genesis_ai.services.pipeline.stages.hydration import FeatureHydrator
from genesis_ai.services.pipeline.types import AuthorInfo, Candidate


class DummyGemini:
    async def analyze_comment(self, text: str):
        return {
            "purchase_intent": 0.0,
            "reply_inducing": 0.0,
            "constructive_feedback": 0.0,
            "sentiment_intensity": 0.0,
            "toxicity": 0.0,
            "keywords": [],
            "topics": [],
        }


def build_candidate(idx: int) -> Candidate:
    return Candidate(
        id=str(idx),
        content=f"comment {idx}",
        author=AuthorInfo(username="tester"),
        created_at=None,
        like_count=0,
    )


@pytest.mark.asyncio
async def test_hydrator_uses_semaphore_limit():
    hydrator = FeatureHydrator(DummyGemini())
    hydrator.MAX_CONCURRENT = 2
    hydrator._semaphore = asyncio.Semaphore(hydrator.MAX_CONCURRENT)

    active = 0
    max_active = 0

    async def fake_analyze(candidate):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return candidate

    hydrator._analyze_single_comment = fake_analyze

    candidates = [build_candidate(i) for i in range(5)]
    await hydrator.hydrate(candidates)

    assert max_active <= 2
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_feature_hydrator_semaphore.py -v`
Expected: FAIL (no semaphore wrapper, max_active > 2)

**Step 3: Write minimal implementation**

- `hydration.py`에 `MAX_CONCURRENT = 10` 추가
- `__init__`에 `self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)` 추가
- `_analyze_with_semaphore` 래퍼 추가
- `hydrate`에서 `self._analyze_with_semaphore` 사용

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_feature_hydrator_semaphore.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/genesis_ai/services/pipeline/stages/hydration.py tests/unit/test_feature_hydrator_semaphore.py
git commit -m "fix: limit hydration concurrency with semaphore"
```
