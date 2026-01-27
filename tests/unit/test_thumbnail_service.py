import pytest

from genesis_ai.core.exceptions import ThumbnailGenerationError
from genesis_ai.services.thumbnail_service import ThumbnailService


class _DummyImageClient:
    def __init__(self, result=b"img"):
        self.result = result
        self.calls = []

    def generate_image(self, prompt, aspect_ratio="16:9"):
        self.calls.append({"prompt": prompt, "aspect_ratio": aspect_ratio})
        return self.result


def test_generate_uses_client_and_aspect_ratio():
    client = _DummyImageClient(result=b"img")
    service = ThumbnailService(client=client)

    image = service.generate(
        product={"name": "Widget", "category": "Gadgets"},
        hook_text="Best deal",
        style="dramatic",
    )

    assert image == b"img"
    assert client.calls[0]["aspect_ratio"] == "9:16"
    assert "Widget" in client.calls[0]["prompt"]


def test_generate_raises_on_empty_result():
    client = _DummyImageClient(result=None)
    service = ThumbnailService(client=client)

    with pytest.raises(ThumbnailGenerationError):
        service.generate(
            product={"name": "Widget", "category": "Gadgets"},
            hook_text="Best deal",
            style="dramatic",
        )


def test_generate_multiple_returns_styles():
    client = _DummyImageClient(result=b"img")
    service = ThumbnailService(client=client)

    results = service.generate_multiple(
        product={"name": "Widget"},
        hook_texts=["A", "B"],
        styles=["dramatic", "vibrant"],
    )

    assert len(results) == 2
    assert results[0]["style"] == "dramatic"
    assert results[1]["style"] == "vibrant"
    assert results[0]["image"] == b"img"


def test_generate_from_strategy_default_hook():
    client = _DummyImageClient(result=b"img")
    service = ThumbnailService(client=client)

    results = service.generate_from_strategy(
        product={"name": "Widget"},
        strategy={},
        count=1,
        styles=["dramatic"],
    )

    assert len(results) == 1
