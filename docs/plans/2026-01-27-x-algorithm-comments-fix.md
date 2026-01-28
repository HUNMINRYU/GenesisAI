# X-Algorithm Comments Field Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** YouTube 수집 데이터에 댓글 리스트를 포함시켜 X-Algorithm 인사이트가 0건이 되는 버그를 해결한다.

**Architecture:** YoutubeClient.collect_video_data()에서 이미 수집된 comments 리스트를 collected_videos 항목에 추가한다. 데이터 흐름은 기존 구조를 유지하며 1줄만 추가한다.

**Tech Stack:** Python, pytest

---

### Task 1: YouTube 수집 데이터에 comments 필드 추가

**Files:**
- Modify: `src/genesis_ai/infrastructure/clients/youtube_client.py`

**Step 1: Write the failing test**

```python
from genesis_ai.infrastructure.clients.youtube_client import YouTubeClient


def test_collect_video_data_includes_comments(mocker):
    client = YouTubeClient(api_key="test")

    mocker.patch.object(client, "search_videos", return_value=[{"id": "v1", "title": "t", "description": "d"}])
    mocker.patch.object(client, "get_video_transcript", return_value="tx")
    mocker.patch.object(client, "get_video_comments", return_value=[{"text": "c1"}])

    data = client.collect_video_data(keyword="k", max_results=1, include_comments=True)

    assert data["videos"][0]["comments"] == [{"text": "c1"}]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_youtube_client_comments.py -v`
Expected: FAIL with missing "comments" key

**Step 3: Write minimal implementation**

- `collect_video_data`의 `collected_videos.append({...})`에 `"comments": comments,` 추가

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_youtube_client_comments.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/genesis_ai/infrastructure/clients/youtube_client.py tests/unit/test_youtube_client_comments.py
git commit -m "fix: include youtube comments in collected videos"
```
