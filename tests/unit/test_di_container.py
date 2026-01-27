"""
DI 컨테이너 오버라이드 검증 테스트
"""

import pytest

from genesis_ai.config.dependencies import ServiceContainer, override_services
from genesis_ai.core.interfaces.api_client import INaverClient
from genesis_ai.core.interfaces.services import IHookService


class _BadClient:
    pass


class _GoodNaverClient:
    def is_configured(self) -> bool:
        return True

    def health_check(self) -> bool:
        return True

    def search(self, query: str, max_results: int = 10):
        return []

    def search_shopping(self, query: str, display: int = 10):
        return []

    def analyze_competitors(self, products: list[dict]) -> dict:
        return {}


def test_override_rejects_invalid_protocol():
    container = ServiceContainer(settings=object(), overrides={"naver_client": _BadClient()})
    with pytest.raises(TypeError):
        _ = container.naver_client


def test_override_accepts_protocol():
    container = ServiceContainer(settings=object(), overrides={"naver_client": _GoodNaverClient()})
    client = container.naver_client
    assert isinstance(client, INaverClient)


class _StubService:
    def get_available_styles(self):
        return []

    def generate_hooks(self, style, product, pain_points=None, count=3):
        return []

    def generate_multi_style_hooks(self, product, pain_points=None, styles=None):
        return {}

    def get_best_hooks_for_video(self, product, video_style="dramatic", pain_points=None):
        return []


def test_service_override_wins():
    stub = _StubService()
    container = ServiceContainer(settings=object(), overrides={"hook_service": stub})
    assert container.hook_service is stub
    assert isinstance(container.hook_service, IHookService)


def test_override_context_manager():
    stub = _StubService()
    with override_services(overrides={"hook_service": stub}, settings=object()) as container:
        assert container.hook_service is stub
        assert ServiceContainer.get_instance() is container
