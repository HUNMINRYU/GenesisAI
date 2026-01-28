from genesis_ai.services.youtube_service import YouTubeService


class _DummyYouTubeClient:
    def __init__(self) -> None:
        self.search_calls = 0
        self.collect_calls = 0
        self.pain_calls = 0
        self.gain_calls = 0

    def search(self, query: str, max_results: int = 10) -> list[dict]:
        self.search_calls += 1
        return [{"id": "v1", "title": "video"}][:max_results]

    def get_video_details(self, video_id: str) -> dict | None:
        return {"id": video_id, "title": "detail"}

    def get_video_comments(self, video_id: str, max_results: int = 100) -> list[dict]:
        return [{"id": "c1", "text": "좋아요"}]

    def get_transcript(self, video_id: str) -> str | None:
        return "transcript"

    def collect_video_data(
        self,
        product: dict,
        max_results: int = 5,
        include_comments: bool = True,
    ) -> dict:
        self.collect_calls += 1
        return {
            "videos": [{"id": "v1"}],
            "comments": [{"id": "c1", "text": "좋아요"}] if include_comments else [],
        }

    def extract_pain_points(self, comments: list[dict]) -> list[dict]:
        self.pain_calls += 1
        return [{"text": "불편함"}]

    def extract_gain_points(self, comments: list[dict]) -> list[dict]:
        self.gain_calls += 1
        return [{"text": "만족"}]


def test_youtube_service_collect_and_analyze():
    client = _DummyYouTubeClient()
    service = YouTubeService(client=client)

    service.search_videos.invalidate_cache()
    first = service.search_videos("테스트", max_results=1)
    second = service.search_videos("테스트", max_results=1)

    assert first == second
    assert client.search_calls == 1

    data = service.collect_product_data(
        product={"name": "Test"},
        max_results=1,
        include_comments=True,
    )

    assert data["videos"]
    assert data["comments"]
    assert client.collect_calls == 1

    analysis = service.analyze_comments(data["comments"])
    assert analysis["pain_points"]
    assert analysis["gain_points"]
    assert client.pain_calls == 1
    assert client.gain_calls == 1
