"""
서비스 에러 래핑 테스트
"""

import pytest

from genesis_ai.core.exceptions import DataCollectionError, StrategyGenerationError
from genesis_ai.services.marketing_service import MarketingService
from genesis_ai.services.naver_service import NaverService
from genesis_ai.services.youtube_service import YouTubeService


class _FailingYouTubeClient:
    def search(self, query, max_results):
        raise Exception("boom")


class _FailingNaverClient:
    def search_shopping(self, query, max_results):
        raise Exception("boom")


class _FailingGeminiClient:
    def analyze_marketing_data(self, **kwargs):
        raise Exception("boom")


def test_youtube_search_wraps_error():
    service = YouTubeService(client=_FailingYouTubeClient())
    with pytest.raises(DataCollectionError) as exc:
        service.search_videos("test")
    assert exc.value.original_error is not None


def test_naver_search_wraps_error():
    service = NaverService(client=_FailingNaverClient())
    with pytest.raises(DataCollectionError) as exc:
        service.search_products("test")
    assert exc.value.original_error is not None


def test_marketing_analyze_wraps_error():
    service = MarketingService(client=_FailingGeminiClient())
    with pytest.raises(StrategyGenerationError) as exc:
        service.analyze_data({}, {}, "test")
    assert exc.value.original_error is not None
