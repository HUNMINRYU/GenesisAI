from genesis_ai.infrastructure.clients.youtube_client import YouTubeClient


def test_collect_video_data_includes_comments(monkeypatch):
    client = YouTubeClient(api_key="test")

    monkeypatch.setattr(
        client,
        "search",
        lambda keyword, max_results: [
            {"id": "v1", "title": "t", "description": "d"}
        ],
    )
    monkeypatch.setattr(client, "get_transcript", lambda video_id: "tx")
    monkeypatch.setattr(
        client, "get_video_comments", lambda video_id, max_results=30: [{"text": "c1"}]
    )

    data = client.collect_video_data(
        product={"name": "p", "target": "t", "category": "c"},
        max_results=1,
        include_comments=True,
    )

    assert data["videos"][0]["comments"] == [{"text": "c1"}]
