import asyncio

from genesis_ai.services.pipeline.orchestrator import PipelineOrchestrator
from genesis_ai.services.pipeline.stages.filter import QualityFilter
from genesis_ai.services.pipeline.stages.hydration import FeatureHydrator
from genesis_ai.services.pipeline.stages.scorer import EngagementScorer
from genesis_ai.services.pipeline.stages.selector import TopInsightSelector
from genesis_ai.services.pipeline.stages.source import CommentSource


class _DummyMarketingAIService:
    async def generate_content_async(self, prompt: str) -> str:
        return """
        {
            "purchase_intent": 0.9,
            "reply_inducing": 0.6,
            "constructive_feedback": 0.7,
            "sentiment_intensity": 0.4,
            "toxicity": 0.1,
            "keywords": ["가성비", "추천"]
        }
        """.strip()


def test_pipeline_orchestrator_end_to_end():
    source = CommentSource()
    hydrator = FeatureHydrator(_DummyMarketingAIService())
    quality_filter = QualityFilter()
    scorer = EngagementScorer()
    selector = TopInsightSelector()

    orchestrator = PipelineOrchestrator(
        source=source,
        hydrator=hydrator,
        quality_filter=quality_filter,
        scorer=scorer,
        selector=selector,
    )

    raw_data = [
        {"id": "1", "author": "user1", "text": "정말 만족합니다. 추천해요!", "likes": 12},
        {"id": "2", "author": "user2", "text": "짧음", "likes": 0},
        {"id": "3", "author": "user3", "text": "광고 문의는 카톡", "likes": 3},
    ]

    result = asyncio.run(orchestrator.run_pipeline(raw_data))

    assert result["insights"]
    assert result["stats"]["original_count"] == 3
    assert result["stats"]["filtered_count"] == 1
    assert result["stats"]["post_filtered_count"] == 1
    assert result["stats"]["processed_count"] == 1
