# Filter Logging Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 필터링 사유별 통계를 기록하고 로그로 출력해 원인 분석이 가능하도록 한다.

**Architecture:** QualityFilter 내부에 stats를 유지하고, filter 호출 시 사유별 카운트를 누적한다. 필터링 결과를 log_info로 출력하고 외부 조회를 위해 get_stats를 제공한다.

**Tech Stack:** Python, pytest

---

### Task 1: QualityFilter 통계/로깅 기능 추가

**Files:**
- Modify: `src/genesis_ai/services/pipeline/stages/filter.py`
- Create: `tests/unit/test_quality_filter_stats.py`

**Step 1: Write the failing test**

```python
from datetime import datetime

import pytest

from genesis_ai.services.pipeline.stages.filter import QualityFilter
from genesis_ai.services.pipeline.types import AuthorInfo, Candidate, CandidateFeatures


def build_candidate(content: str, toxicity: float = 0.0):
    return Candidate(
        id="1",
        content=content,
        author=AuthorInfo(username="tester"),
        created_at=datetime.utcnow(),
        like_count=0,
        features=CandidateFeatures(toxicity=toxicity),
    )


def test_quality_filter_stats_counts_and_get_stats():
    candidates = [
        build_candidate("짧"),  # too_short
        build_candidate("이건 광고입니다"),  # spam
        build_candidate("정상 문장", toxicity=0.9),  # toxic
        build_candidate("정상 문장입니다"),  # passed
    ]

    qf = QualityFilter()
    result = qf.filter(candidates)

    assert len(result) == 1
    stats = qf.get_stats()
    assert stats["too_short"] == 1
    assert stats["spam"] == 1
    assert stats["toxic"] == 1
    assert stats["passed"] == 1


def test_quality_filter_logs_summary(caplog):
    candidates = [build_candidate("정상 문장입니다")]
    qf = QualityFilter()

    with caplog.at_level("INFO"):
        qf.filter(candidates)

    assert any("QualityFilter 결과" in record.message for record in caplog.records)
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_quality_filter_stats.py -v`
Expected: FAIL with missing stats/get_stats/logs

**Step 3: Write minimal implementation**

- `QualityFilter.__init__`에서 `self.stats` 초기화
- `filter`에서 `_check_eligibility`로 사유 분류
- 통과/탈락 카운트 누적
- `log_info`로 결과 요약 출력
- `get_stats()` 메서드 추가

```python
from typing import List, Optional

from genesis_ai.services.pipeline.types import Candidate
from genesis_ai.utils.logger import log_info


class QualityFilter:
    MIN_LENGTH = 5
    SPAM_KEYWORDS = ["광고", "홍보", "http", "카톡", "사다리", "토토"]

    def __init__(self):
        self.stats = {"too_short": 0, "spam": 0, "toxic": 0, "passed": 0}

    def filter(self, candidates: List[Candidate]) -> List[Candidate]:
        self._reset_stats()
        filtered_candidates = []
        for candidate in candidates:
            reason = self._check_eligibility(candidate)
            if reason is None:
                filtered_candidates.append(candidate)
                self.stats["passed"] += 1
            else:
                self.stats[reason] += 1

        log_info(
            f"QualityFilter 결과: 입력 {len(candidates)}건 → 통과 {self.stats['passed']}건"
        )
        log_info(f"  - 길이 미달: {self.stats['too_short']}건")
        log_info(f"  - 스팸 키워드: {self.stats['spam']}건")
        log_info(f"  - 독성 초과: {self.stats['toxic']}건")

        return filtered_candidates

    def _check_eligibility(self, candidate: Candidate) -> Optional[str]:
        if len(candidate.content.strip()) < self.MIN_LENGTH:
            return "too_short"
        for keyword in self.SPAM_KEYWORDS:
            if keyword in candidate.content:
                return "spam"
        if candidate.features.toxicity > 0.8:
            return "toxic"
        return None

    def _reset_stats(self):
        self.stats = {"too_short": 0, "spam": 0, "toxic": 0, "passed": 0}

    def get_stats(self) -> dict:
        return self.stats.copy()
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_quality_filter_stats.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/genesis_ai/services/pipeline/stages/filter.py tests/unit/test_quality_filter_stats.py
git commit -m "feat: add quality filter stats logging"
```
