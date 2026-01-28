import pytest

from genesis_ai.core.exceptions import StrategyGenerationError
from genesis_ai.services.marketing_service import MarketingService


class _DummyMarketingAIService:
    def __init__(self) -> None:
        self.analyze_calls = 0
        self.strategy_calls = 0

    def analyze_marketing_data(
        self,
        youtube_data: dict,
        naver_data: dict,
        product_name: str,
        top_insights: list[dict] = None,
        progress_callback=None,
        use_search_grounding: bool = True,
    ) -> dict:
        self.analyze_calls += 1
        return {
            "target_audience": {"primary": "A"},
            "hook_suggestions": ["hook-1"],
            "keywords": ["k1"],
            "summary": "ok",
        }

    def generate_marketing_strategy(self, collected_data: dict, progress_callback=None):
        self.strategy_calls += 1
        return {"hook_suggestions": ["hook-2"], "summary": "ok"}

    def generate_hook_texts(
        self,
        product_name: str,
        hook_types: list[str] | None = None,
        count: int = 5,
        custom_params: dict | None = None,
    ) -> list[dict]:
        return [{"text": "hook", "type": "default"}]


def test_marketing_service_analyze_and_strategy():
    client = _DummyMarketingAIService()
    service = MarketingService(client=client)

    analysis = service.analyze_data(
        youtube_data={"videos": []},
        naver_data={"products": []},
        product_name="Test",
        top_insights=[],
        use_grounding=False,
    )

    assert analysis["summary"] == "ok"
    assert client.analyze_calls == 1

    strategy = service.generate_strategy(collected_data={"product": {"name": "Test"}})
    assert strategy["hook_suggestions"] == ["hook-2"]
    assert client.strategy_calls == 1


def test_marketing_service_raises_on_error_response():
    class _ErrorClient(_DummyMarketingAIService):
        def analyze_marketing_data(self, *args, **kwargs):
            return {"error": "fail"}

    service = MarketingService(client=_ErrorClient())

    with pytest.raises(StrategyGenerationError):
        service.analyze_data(
            youtube_data={},
            naver_data={},
            product_name="Test",
        )
