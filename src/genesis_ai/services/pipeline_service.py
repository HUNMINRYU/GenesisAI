"""
파이프라인 서비스
전체 마케팅 파이프라인 오케스트레이션
"""
import time
from typing import Callable, Optional

from ..core.exceptions import PipelineError
from ..core.interfaces import IStorageService
from ..core.models import (
    CollectedData,
    GeneratedContent,
    PipelineConfig,
    PipelineProgress,
    PipelineResult,
    PipelineStep,
)
from ..utils.logger import get_logger
from .marketing_service import MarketingService
from .naver_service import NaverService
from .thumbnail_service import ThumbnailService
from .video_service import VideoService
from .youtube_service import YouTubeService

logger = get_logger(__name__)


class PipelineService:
    """파이프라인 오케스트레이션 서비스"""

    def __init__(
        self,
        youtube_service: YouTubeService,
        naver_service: NaverService,
        marketing_service: MarketingService,
        thumbnail_service: ThumbnailService,
        video_service: VideoService,
        storage_service: IStorageService,
    ) -> None:
        self._youtube = youtube_service
        self._naver = naver_service
        self._marketing = marketing_service
        self._thumbnail = thumbnail_service
        self._video = video_service
        self._storage = storage_service

    def execute(
        self,
        product: dict,
        config: PipelineConfig,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
    ) -> PipelineResult:
        """파이프라인 실행"""
        logger.info(f"파이프라인 실행 시작: {product.get('name', 'N/A')}")
        start_time = time.time()

        progress = PipelineProgress()
        collected_data = CollectedData()
        generated_content = GeneratedContent()
        strategy: dict = {}

        def update_progress(step: PipelineStep, message: str = "") -> None:
            progress.update(step, message)
            if progress_callback:
                progress_callback(progress)

        try:
            # Step 1: 데이터 수집
            update_progress(PipelineStep.DATA_COLLECTION, "데이터 수집 시작")

            # YouTube 데이터 수집
            update_progress(PipelineStep.YOUTUBE_COLLECTION, "YouTube 데이터 수집 중...")
            youtube_data = self._youtube.collect_product_data(
                product=product,
                max_results=config.youtube_count,
                include_comments=config.include_comments,
            )
            collected_data.youtube_data = youtube_data
            collected_data.pain_points = youtube_data.get("pain_points", [])
            collected_data.gain_points = youtube_data.get("gain_points", [])

            # Naver 데이터 수집
            update_progress(PipelineStep.NAVER_COLLECTION, "네이버 쇼핑 데이터 수집 중...")
            naver_data = self._naver.collect_product_data(
                product=product,
                max_results=config.naver_count,
            )
            collected_data.naver_data = naver_data

            # Step 2: 마케팅 전략 생성
            update_progress(PipelineStep.STRATEGY_GENERATION, "마케팅 전략 생성 중...")
            strategy = self._marketing.generate_strategy(
                collected_data={
                    "product": product,
                    "youtube_data": youtube_data,
                    "naver_data": naver_data,
                },
            )

            # Step 3: 썸네일 생성
            if config.generate_thumbnail:
                update_progress(PipelineStep.THUMBNAIL_CREATION, "썸네일 생성 중...")

                if config.generate_multi_thumbnails:
                    thumbnails = self._thumbnail.generate_from_strategy(
                        product=product,
                        strategy=strategy,
                        count=config.thumbnail_count,
                    )
                    generated_content.multi_thumbnails = thumbnails
                    if thumbnails:
                        generated_content.thumbnail_data = thumbnails[0].get("image")
                else:
                    hooks = strategy.get("hook_suggestions", [])
                    hook_text = hooks[0] if hooks else f"{product.get('name', '제품')}!"
                    thumbnail = self._thumbnail.generate(
                        product=product,
                        hook_text=hook_text,
                    )
                    generated_content.thumbnail_data = thumbnail

            # Step 4: 비디오 생성
            if config.generate_video:
                update_progress(PipelineStep.VIDEO_GENERATION, "비디오 생성 중...")
                video_result = self._video.generate_marketing_video(
                    product=product,
                    strategy=strategy,
                    duration_seconds=config.video_duration,
                )

                if isinstance(video_result, bytes):
                    generated_content.video_path = "generated"
                else:
                    generated_content.video_url = video_result

            # Step 5: 업로드 (옵션)
            if config.upload_to_gcs:
                update_progress(PipelineStep.UPLOAD, "GCS 업로드 중...")
                # TODO: GCS 업로드 구현

            # 완료
            update_progress(PipelineStep.COMPLETED, "파이프라인 완료!")
            duration = time.time() - start_time

            logger.info(f"파이프라인 실행 완료: {duration:.2f}초")

            return PipelineResult(
                success=True,
                product_name=product.get("name", ""),
                config=config,
                collected_data=collected_data,
                strategy=strategy,
                generated_content=generated_content,
                duration_seconds=duration,
            )

        except Exception as e:
            logger.error(f"파이프라인 실행 실패: {e}")
            update_progress(PipelineStep.FAILED, str(e))
            duration = time.time() - start_time

            return PipelineResult(
                success=False,
                product_name=product.get("name", ""),
                config=config,
                collected_data=collected_data,
                strategy=strategy,
                generated_content=generated_content,
                error_message=str(e),
                duration_seconds=duration,
            )

    def execute_data_collection_only(
        self,
        product: dict,
        config: PipelineConfig,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> CollectedData:
        """데이터 수집만 실행"""
        logger.info(f"데이터 수집 시작: {product.get('name', 'N/A')}")

        collected_data = CollectedData()

        try:
            if progress_callback:
                progress_callback("YouTube 데이터 수집 중...", 20)

            youtube_data = self._youtube.collect_product_data(
                product=product,
                max_results=config.youtube_count,
                include_comments=config.include_comments,
            )
            collected_data.youtube_data = youtube_data
            collected_data.pain_points = youtube_data.get("pain_points", [])
            collected_data.gain_points = youtube_data.get("gain_points", [])

            if progress_callback:
                progress_callback("네이버 쇼핑 데이터 수집 중...", 60)

            naver_data = self._naver.collect_product_data(
                product=product,
                max_results=config.naver_count,
            )
            collected_data.naver_data = naver_data

            if progress_callback:
                progress_callback("데이터 수집 완료", 100)

            return collected_data

        except Exception as e:
            logger.error(f"데이터 수집 실패: {e}")
            raise PipelineError(f"데이터 수집 실패: {e}")
