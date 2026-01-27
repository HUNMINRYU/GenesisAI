import asyncio

import pytest

from genesis_ai.services.pipeline.stages.hydration import FeatureHydrator
from genesis_ai.services.pipeline.types import AuthorInfo, Candidate


class DummyGemini:
    async def generate_content_async(self, prompt: str):
        return """
        {
            "purchase_intent": 0.0,
            "reply_inducing": 0.0,
            "constructive_feedback": 0.0,
            "sentiment_intensity": 0.0,
            "toxicity": 0.0,
            "keywords": [],
            "topics": []
        }
        """


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
