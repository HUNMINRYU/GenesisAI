from unittest.mock import AsyncMock

import pytest

from genesis_ai.services.pipeline.orchestrator import PipelineOrchestrator
from genesis_ai.services.pipeline.stages.filter import QualityFilter
from genesis_ai.services.pipeline.stages.hydration import FeatureHydrator
from genesis_ai.services.pipeline.stages.scorer import EngagementScorer
from genesis_ai.services.pipeline.stages.selector import TopInsightSelector
from genesis_ai.services.pipeline.stages.source import CommentSource


@pytest.fixture
def mock_gemini_client():
    client = AsyncMock()
    # Mock response for Gemini
    client.generate_content_async.return_value = """
    ```json
    {
        "purchase_intent": 0.9,
        "reply_inducing": 0.5,
        "constructive_feedback": 0.8,
        "sentiment_intensity": 0.7,
        "toxicity": 0.1,
        "keywords": ["구매", "추천"]
    }
    ```
    """
    return client

@pytest.fixture
def pipeline_orchestrator(mock_gemini_client):
    source = CommentSource()
    hydrator = FeatureHydrator(mock_gemini_client)
    quality_filter = QualityFilter()
    scorer = EngagementScorer()
    selector = TopInsightSelector()

    return PipelineOrchestrator(
        source=source,
        hydrator=hydrator,
        quality_filter=quality_filter,
        scorer=scorer,
        selector=selector
    )

@pytest.mark.asyncio
async def test_pipeline_full_run(pipeline_orchestrator):
    # Given: Raw data
    raw_data = [
        {"author": "user1", "text": "이거 진짜 좋네요! 구매하고 싶어요.", "likes": 10},
        {"author": "user2", "text": "너무 짧음", "likes": 1},  # Filtered out (length)
        {"author": "user3", "text": "스팸 광고입니다. http://spam.com", "likes": 0},  # Filtered out (keyword)
        {"author": "user4", "text": "상당히 구체적인 피드백입니다. 이 부분이 아쉽네요.", "likes": 5},
    ]

    # When: Run pipeline
    result = await pipeline_orchestrator.run_pipeline(raw_data)

    # Then: Verify results
    assert "insights" in result
    assert "stats" in result
    assert result["stats"]["original_count"] == 4
    # user3 (spam) should be filtered.
    # user2 ("너무 짧음") has length 5, and MIN_LENGTH is 5. 5 < 5 is False, so it's NOT filtered.
    assert result["stats"]["filtered_count"] == 3
    assert len(result["insights"]) <= 5

    # Check if insights contain expected content
    contents = [i["content"] for i in result["insights"]]
    assert "이거 진짜 좋네요! 구매하고 싶어요." in contents
    assert "상당히 구체적인 피드백입니다. 이 부분이 아쉽네요." in contents

@pytest.mark.asyncio
async def test_pipeline_empty_data(pipeline_orchestrator):
    result = await pipeline_orchestrator.run_pipeline([])
    assert result["insights"] == []
    assert result["stats"]["original_count"] == 0

@pytest.mark.asyncio
async def test_pipeline_all_filtered(pipeline_orchestrator):
    raw_data = [
        {"author": "user1", "text": "짦음", "likes": 0}, # Length 2 < 5
    ]
    result = await pipeline_orchestrator.run_pipeline(raw_data)
    assert result["insights"] == []
    assert result["stats"]["filtered_count"] == 0
