
from genesis_ai.core.models import PipelineConfig, UploadStatus
from genesis_ai.services.pipeline_service import PipelineService


class _DummyYouTubeService:
    def __init__(self) -> None:
        self.calls = 0

    def collect_product_data(self, product, max_results, include_comments):
        self.calls += 1
        return {
            "videos": [{"id": "v1"}],
            "pain_points": [{"text": "pain"}],
            "gain_points": [{"text": "gain"}],
        }


class _DummyNaverService:
    def __init__(self) -> None:
        self.calls = 0

    def collect_product_data(self, product, max_results):
        self.calls += 1
        return {
            "products": [{"id": "p1"}],
            "competitor_stats": {"min_price": 1000},
            "total_count": 1,
        }


class _DummyMarketingService:
    def __init__(self) -> None:
        self.calls = 0

    def generate_strategy(self, collected_data):
        self.calls += 1
        return {"hook_suggestions": ["hook-1"], "summary": "ok"}


class _DummyThumbnailService:
    def __init__(self) -> None:
        self.multi_calls = 0
        self.single_calls = 0

    def generate_from_strategy(self, product, strategy, count, styles):
        self.multi_calls += 1
        return [
            {"image": b"\x89PNG\r\n\x1a\nimage-1", "style": "dramatic"},
            {"image": b"\x89PNG\r\n\x1a\nimage-2", "style": "neobrutalism"},
            {"image": b"\x89PNG\r\n\x1a\nimage-3", "style": "vibrant"},
        ][:count]

    def generate(self, product, hook_text):
        self.single_calls += 1
        return b"\x89PNG\r\n\x1a\nsingle"


class _DummyVideoService:
    def __init__(self) -> None:
        self.calls = 0

    def generate_marketing_video(
        self,
        product,
        strategy,
        duration_seconds,
        mode="single",
        phase2_prompt=None,
        enable_dual_phase_beta=False,
        progress_callback=None,
    ):
        self.calls += 1
        return b"0000ftypvideo-bytes"


class _DummyPipelineOrchestrator:
    async def run_pipeline(self, raw_data):
        return {
            "insights": [{"rank": 1, "score": 1.0, "content": "ok"}],
            "stats": {"original_count": len(raw_data), "filtered_count": len(raw_data)},
        }


class _DummyHistoryService:
    def __init__(self) -> None:
        self.saved = []

    def save_result(self, result):
        self.saved.append(result)
        return "saved.json"


class _DummySocialService:
    async def generate_posts(self, product, strategy, top_insights=None):
        return [{"platform": "instagram", "content": "post"}]


class _DummyStorage:
    def __init__(self) -> None:
        self.uploads = []
        self.bucket_name = "test-bucket"

    def ensure_bucket(self) -> None:
        return None

    def health_check(self) -> bool:
        return True

    def upload(self, data, path, content_type="application/json"):
        self.uploads.append({"path": path, "content_type": content_type, "data": data})
        return True

    def download(self, path):
        return None

    def list_files(self, prefix=""):
        return []

    def get_public_url(self, path):
        return None

    def delete(self, path):
        return True

    def exists(self, path):
        return False


def test_pipeline_execute_success_with_uploads():
    service = PipelineService(
        youtube_service=_DummyYouTubeService(),
        naver_service=_DummyNaverService(),
        marketing_service=_DummyMarketingService(),
        thumbnail_service=_DummyThumbnailService(),
        video_service=_DummyVideoService(),
        storage_service=_DummyStorage(),
        pipeline_orchestrator=_DummyPipelineOrchestrator(),
        history_service=_DummyHistoryService(),
        social_media_service=_DummySocialService(),
    )

    config = PipelineConfig(
        youtube_count=3,
        naver_count=10,
        include_comments=True,
        generate_social=False,
        generate_thumbnail=True,
        generate_multi_thumbnails=True,
        thumbnail_count=3,
        generate_video=True,
        upload_to_gcs=True,
    )

    result = service.execute(product={"name": "TestProduct"}, config=config)

    assert result.success is True
    assert result.upload_status is UploadStatus.SUCCESS
    assert result.generated_content is not None
    assert len(result.generated_content.multi_thumbnails) == 3
    assert result.generated_content.thumbnail_data is not None
    assert result.generated_content.video_bytes is not None

    paths = [item["path"] for item in service._storage.uploads]
    assert any(p.endswith("/collected_data.json") for p in paths)
    assert any(p.endswith("/strategy.json") for p in paths)
    assert any(p.endswith("/thumbnail_1.png") for p in paths)
    assert any(p.endswith("/thumbnail_2.png") for p in paths)
    assert any(p.endswith("/thumbnail_3.png") for p in paths)
    assert any(p.endswith("/video.mp4") for p in paths)
    assert any(p.endswith("/metadata.json") for p in paths)


def test_pipeline_execute_skips_optional_steps():
    youtube = _DummyYouTubeService()
    naver = _DummyNaverService()
    marketing = _DummyMarketingService()

    class _FailingThumbnailService:
        def generate_from_strategy(self, *args, **kwargs):
            raise AssertionError("thumbnail should not be called")

        def generate(self, *args, **kwargs):
            raise AssertionError("thumbnail should not be called")

    class _FailingVideoService:
        def generate_marketing_video(self, *args, **kwargs):
            raise AssertionError("video should not be called")

    storage = _DummyStorage()

    service = PipelineService(
        youtube_service=youtube,
        naver_service=naver,
        marketing_service=marketing,
        thumbnail_service=_FailingThumbnailService(),
        video_service=_FailingVideoService(),
        storage_service=storage,
        pipeline_orchestrator=_DummyPipelineOrchestrator(),
        history_service=_DummyHistoryService(),
        social_media_service=_DummySocialService(),
    )

    config = PipelineConfig(
        generate_thumbnail=False,
        generate_video=False,
        upload_to_gcs=False,
        generate_social=False,
    )

    result = service.execute(product={"name": "TestProduct"}, config=config)

    assert result.success is True
    assert result.upload_status is UploadStatus.SKIPPED
    assert youtube.calls == 1
    assert naver.calls == 1
    assert marketing.calls == 1
    assert storage.uploads == []


def test_pipeline_execute_handles_error():
    class _FailingYouTubeService:
        def collect_product_data(self, product, max_results, include_comments):
            raise RuntimeError("boom")

    service = PipelineService(
        youtube_service=_FailingYouTubeService(),
        naver_service=_DummyNaverService(),
        marketing_service=_DummyMarketingService(),
        thumbnail_service=_DummyThumbnailService(),
        video_service=_DummyVideoService(),
        storage_service=_DummyStorage(),
        pipeline_orchestrator=_DummyPipelineOrchestrator(),
        history_service=_DummyHistoryService(),
        social_media_service=_DummySocialService(),
    )

    result = service.execute(
        product={"name": "TestProduct"},
        config=PipelineConfig(generate_social=False),
    )

    assert result.success is False
    assert result.upload_status in {UploadStatus.SKIPPED, UploadStatus.FAILED}
    assert "boom" in (result.error_message or "")


def test_pipeline_execute_marks_upload_failed_on_health_check():
    class _FailingStorage(_DummyStorage):
        def health_check(self) -> bool:
            return False

    service = PipelineService(
        youtube_service=_DummyYouTubeService(),
        naver_service=_DummyNaverService(),
        marketing_service=_DummyMarketingService(),
        thumbnail_service=_DummyThumbnailService(),
        video_service=_DummyVideoService(),
        storage_service=_FailingStorage(),
        pipeline_orchestrator=_DummyPipelineOrchestrator(),
        history_service=_DummyHistoryService(),
        social_media_service=_DummySocialService(),
    )

    config = PipelineConfig(generate_social=False, upload_to_gcs=True)

    result = service.execute(product={"name": "TestProduct"}, config=config)

    assert result.success is True
    assert result.upload_status is UploadStatus.FAILED
    assert result.upload_errors


def test_pipeline_execute_marks_partial_uploads():
    class _FailingStorage(_DummyStorage):
        def upload(self, data, path, content_type="application/json"):
            if path.endswith("/strategy.json"):
                raise RuntimeError("boom")
            return super().upload(data, path, content_type)

    service = PipelineService(
        youtube_service=_DummyYouTubeService(),
        naver_service=_DummyNaverService(),
        marketing_service=_DummyMarketingService(),
        thumbnail_service=_DummyThumbnailService(),
        video_service=_DummyVideoService(),
        storage_service=_FailingStorage(),
        pipeline_orchestrator=_DummyPipelineOrchestrator(),
        history_service=_DummyHistoryService(),
        social_media_service=_DummySocialService(),
    )

    result = service.execute(
        product={"name": "TestProduct"},
        config=PipelineConfig(generate_social=False, upload_to_gcs=True),
    )

    assert result.success is True
    assert result.upload_status is UploadStatus.PARTIAL
    assert any("strategy.json" in err for err in result.upload_errors)
