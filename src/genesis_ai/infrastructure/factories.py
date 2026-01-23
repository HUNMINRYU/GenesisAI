"""
의존성 주입 팩토리
모든 서비스 및 클라이언트 인스턴스 생성 관리
"""

from functools import lru_cache

from ..config.settings import get_settings
from .clients.gemini_client import GeminiClient
from .clients.naver_client import NaverClient
from .clients.veo_client import VeoClient
from .clients.youtube_client import YouTubeClient
from .storage.gcs_storage import GCSStorage


# ============================================================
# Client Factories
# ============================================================


@lru_cache()
def get_youtube_client() -> YouTubeClient:
    """YouTube 클라이언트 팩토리"""
    settings = get_settings()
    return YouTubeClient(api_key=settings.google_api_key)


@lru_cache()
def get_naver_client() -> NaverClient:
    """네이버 클라이언트 팩토리"""
    settings = get_settings()
    return NaverClient(
        client_id=settings.naver.client_id.get_secret_value(),
        client_secret=settings.naver.client_secret.get_secret_value(),
    )


@lru_cache()
def get_gemini_client() -> GeminiClient:
    """Gemini 클라이언트 팩토리"""
    settings = get_settings()
    return GeminiClient(
        project_id=settings.gcp.project_id,
        location=settings.gcp.location,
        text_model=settings.models.gemini_text_model,
        image_model=settings.models.gemini_image_model,
    )


@lru_cache()
def get_veo_client() -> VeoClient:
    """Veo 클라이언트 팩토리"""
    settings = get_settings()
    return VeoClient(
        project_id=settings.gcp.project_id,
        location=settings.gcp.location,
        gcs_bucket_name=settings.gcp.gcs_bucket_name,
        model_id=settings.models.veo_model_id,
    )


@lru_cache()
def get_storage_service() -> GCSStorage:
    """GCS 스토리지 서비스 팩토리"""
    settings = get_settings()
    return GCSStorage(
        bucket_name=settings.gcp.gcs_bucket_name,
        project_id=settings.gcp.project_id,
    )


# ============================================================
# Service Factories
# ============================================================


@lru_cache()
def get_youtube_service():
    """YouTube 서비스 팩토리"""
    from ..services.youtube_service import YouTubeService

    return YouTubeService(client=get_youtube_client())


@lru_cache()
def get_naver_service():
    """네이버 서비스 팩토리"""
    from ..services.naver_service import NaverService

    return NaverService(client=get_naver_client())


@lru_cache()
def get_marketing_service():
    """마케팅 서비스 팩토리"""
    from ..services.marketing_service import MarketingService

    return MarketingService(client=get_gemini_client())


@lru_cache()
def get_thumbnail_service():
    """썸네일 서비스 팩토리"""
    from ..services.thumbnail_service import ThumbnailService

    return ThumbnailService(client=get_gemini_client())


@lru_cache()
def get_video_service():
    """비디오 서비스 팩토리"""
    from ..services.video_service import VideoService

    return VideoService(client=get_veo_client())


@lru_cache()
def get_pipeline_service():
    """파이프라인 서비스 팩토리 (모든 서비스 통합)"""
    from ..services.pipeline_service import PipelineService

    return PipelineService(
        youtube_service=get_youtube_service(),
        naver_service=get_naver_service(),
        marketing_service=get_marketing_service(),
        thumbnail_service=get_thumbnail_service(),
        video_service=get_video_service(),
        storage_service=get_storage_service(),
    )


def clear_all_caches() -> None:
    """모든 팩토리 캐시 초기화 (테스트용)"""
    # 클라이언트
    get_youtube_client.cache_clear()
    get_naver_client.cache_clear()
    get_gemini_client.cache_clear()
    get_veo_client.cache_clear()
    get_storage_service.cache_clear()
    # 서비스
    get_youtube_service.cache_clear()
    get_naver_service.cache_clear()
    get_marketing_service.cache_clear()
    get_thumbnail_service.cache_clear()
    get_video_service.cache_clear()
    get_pipeline_service.cache_clear()
