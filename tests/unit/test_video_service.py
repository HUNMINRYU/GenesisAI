import pytest

from genesis_ai.core.exceptions import VideoGenerationError
from genesis_ai.services.video_service import VideoService


class _DummyVideoClient:
    def __init__(self, result=b"0000ftyp" + b"x" * 2000):
        self.result = result
        self.generate_calls = []

    def generate_video(self, prompt, duration_seconds=8, resolution="720p", progress_callback=None):
        self.generate_calls.append(
            {
                "prompt": prompt,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
            }
        )
        return self.result

    def generate_marketing_prompt(self, product, insights, hook_text):
        return f"prompt:{product.get('name')}:{hook_text}"

    def get_available_motions(self):
        return ["pan", "zoom"]


def test_sanitize_prompt_input_strips_control_chars():
    service = VideoService(client=_DummyVideoClient())
    text = "hello\x00world"
    assert service.sanitize_prompt_input(text) == "helloworld"


def test_validate_video_output():
    service = VideoService(client=_DummyVideoClient())
    assert service.validate_video_output(b"0000ftyp" + b"x" * 2000) is True
    assert service.validate_video_output("gs://bucket/video.mp4") is True
    assert service.validate_video_output("") is False


def test_generate_success_bytes():
    client = _DummyVideoClient(result=b"0000ftyp" + b"x" * 2000)
    service = VideoService(client=client)

    result = service.generate(prompt="ok", duration_seconds=5, resolution="720p")

    assert result.startswith(b"0000ftyp")
    assert len(result) > 1024
    assert client.generate_calls[0]["prompt"] == "ok"


def test_generate_raises_on_invalid_output():
    client = _DummyVideoClient(result=b"bad")
    service = VideoService(client=client)

    with pytest.raises(VideoGenerationError):
        service.generate(prompt="ok")


def test_generate_marketing_video_uses_hook():
    client = _DummyVideoClient(result=b"0000ftyp" + b"x" * 2000)
    service = VideoService(client=client)

    result = service.generate_marketing_video(
        product={"name": "Widget"},
        strategy={"hook_suggestions": ["Hook"]},
        duration_seconds=8,
    )

    assert result.startswith(b"0000ftyp")
    assert len(result) > 1024
    assert "Hook" in client.generate_calls[0]["prompt"]
