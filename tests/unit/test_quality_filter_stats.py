from datetime import datetime

from genesis_ai.services.pipeline.stages.filter import QualityFilter
from genesis_ai.services.pipeline.types import AuthorInfo, Candidate, CandidateFeatures
from genesis_ai.utils.logger import add_log_callback, clear_log_callbacks


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


def test_quality_filter_logs_summary():
    candidates = [build_candidate("정상 문장입니다")]
    qf = QualityFilter()

    messages = []
    add_log_callback(messages.append)
    try:
        qf.filter(candidates)
    finally:
        clear_log_callbacks()

    assert any("QualityFilter 결과" in message for message in messages)
