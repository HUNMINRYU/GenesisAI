from typing import List, Optional

from genesis_ai.services.pipeline.types import Candidate
from genesis_ai.utils.logger import log_info


class QualityFilter:
    """
    X-Algorithm의 Pre-Scoring Filtering 단계
    스팸, 중복, 저품질 콘텐츠를 사전에 제거하여 Scoring 연산 낭비 방지
    """

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
        # 1. 길이 필터
        if len(candidate.content.strip()) < self.MIN_LENGTH:
            return "too_short"

        # 2. 스팸 키워드 필터
        for keyword in self.SPAM_KEYWORDS:
            if keyword in candidate.content:
                return "spam"

        # 3. Toxicity 필터 (이미 Feature가 있다면)
        if candidate.features.toxicity > 0.8:
            return "toxic"

        return None

    def _reset_stats(self):
        self.stats = {"too_short": 0, "spam": 0, "toxic": 0, "passed": 0}

    def get_stats(self) -> dict:
        return self.stats.copy()
