"""
파이프라인 서비스
전체 마케팅 파이프라인 오케스트레이션
"""

import asyncio
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
    UploadStatus,
)
from ..utils.gcs_store import (
    build_gcs_prefix,
    detect_image_ext,
    detect_video_ext,
    gcs_url_for,
)
from ..utils.logger import (
    get_logger,
    log_error,
    log_info,
    log_section,
    log_step,
    log_success,
    log_timing,
    log_warning,
)
from .history_service import HistoryService
from .marketing_service import MarketingService
from .naver_service import NaverService
from .pipeline.orchestrator import PipelineOrchestrator
from .social_service import SocialMediaService
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
        pipeline_orchestrator: PipelineOrchestrator,
        history_service: HistoryService,
        social_media_service: SocialMediaService,
    ) -> None:
        self._youtube = youtube_service
        self._naver = naver_service
        self._marketing = marketing_service
        self._thumbnail = thumbnail_service
        self._video = video_service
        self._storage = storage_service
        self._orchestrator = pipeline_orchestrator
        self._history = history_service
        self._social = social_media_service

    def execute(
        self,
        product: dict,
        config: PipelineConfig,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
    ) -> PipelineResult:
        """파이프라인 실행"""
        log_section(f"파이프라인 실행 시작: {product.get('name', 'N/A')}")
        start_time = time.time()

        progress = PipelineProgress()
        progress.configure_steps(config)
        collected_data = CollectedData()
        generated_content = GeneratedContent()
        strategy: dict = {}
        upload_status = UploadStatus.SKIPPED
        upload_errors: list[str] = []
        upload_enabled = config.upload_to_gcs

        if upload_enabled and not self._storage.health_check():
            log_warning("GCS health check failed - skipping upload.")
            upload_status = UploadStatus.FAILED
            upload_errors.append("GCS health check failed")
            upload_enabled = False

        def update_progress(step: PipelineStep, message: str = "") -> None:
            progress.update(step, message)
            log_step(f"Pipeline Step: {step.name}", "in progress", message)
            if progress_callback:
                progress_callback(progress)

        try:
            # Step 1: 데이터 수집
            update_progress(PipelineStep.DATA_COLLECTION, "데이터 수집 시작")

            # YouTube 데이터 수집
            update_progress(
                PipelineStep.YOUTUBE_COLLECTION, "YouTube 데이터 수집 중..."
            )
            youtube_data = self._youtube.collect_product_data(
                product=product,
                max_results=config.youtube_count,
                include_comments=config.include_comments,
            )
            collected_data.youtube_data = youtube_data
            collected_data.pain_points = youtube_data.get("pain_points", [])
            collected_data.gain_points = youtube_data.get("gain_points", [])

            # Naver 데이터 수집
            update_progress(
                PipelineStep.NAVER_COLLECTION, "네이버 쇼핑 데이터 수집 중..."
            )
            naver_data = self._naver.collect_product_data(
                product=product,
                max_results=config.naver_count,
            )
            collected_data.naver_data = naver_data

            # X-Algorithm: 핵심 인사이트 분석 (새로운 파이프라인 엔진)
            update_progress(PipelineStep.COMMENT_ANALYSIS, "X-Algorithm 인사이트 분석 중...")
            try:
                # 유튜브 댓글 데이터 추출
                comments = []
                if youtube_data and "videos" in youtube_data:
                    for v in youtube_data["videos"]:
                        for c in v.get("comments", []):
                            comments.append({
                                "author": c.get("author", "unknown"),
                                "text": c.get("text", ""),
                                "likes": c.get("likes", 0)
                            })

                # 비동기 오케스트레이터 실행
                analysis_result = self._run_async(
                    self._orchestrator.run_pipeline(comments)
                )

                collected_data.top_insights = analysis_result.get("insights", [])
                log_info(f"X-Algorithm 분석 완료: {len(collected_data.top_insights)}개 인사이트 도출")
            except Exception as e:
                logger.error(f"X-Algorithm 분석 실패: {e}")
                log_error(f"X-Algorithm 분석 중 오류 발생: {e}")

            # Step 2: 마케팅 전략 생성
            update_progress(PipelineStep.STRATEGY_GENERATION, "마케팅 전략 생성 중...")
            strategy = self._marketing.generate_strategy(
                collected_data={
                    "product": product,
                    "youtube_data": youtube_data,
                    "naver_data": naver_data,
                    "top_insights": collected_data.top_insights,
                },
            )

            # Step 2.1: SNS 포스팅 생성 (추가)
            if config.generate_social:
                update_progress(PipelineStep.SOCIAL_GENERATION, "SNS 포스팅 생성 중...")
                try:
                    # 비동기 실행을 위해 별도 루프 사용
                    social_posts = self._run_async(
                        self._social.generate_posts(
                            product=product,
                            strategy=strategy,
                            top_insights=collected_data.top_insights,
                        )
                    )
                    # 전략 데이터에 병합하여 저장 (전달 용이성)
                    strategy["social_posts"] = social_posts
                    log_info("SNS 포스팅 생성 완료")
                except Exception as e:
                    logger.error(f"SNS 포스팅 생성 실패: {e}")
                    log_error(f"SNS 포스팅 생성 중 오류 발생: {e}")

            # Step 3: 썸네일 생성
            if config.generate_thumbnail:
                update_progress(PipelineStep.THUMBNAIL_CREATION, "썸네일 생성 중...")

                if config.generate_multi_thumbnails:
                    styles = ["dramatic", "neobrutalism", "vibrant", "minimal", "professional"]
                    thumbnails = self._thumbnail.generate_from_strategy(
                        product=product,
                        strategy=strategy,
                        count=config.thumbnail_count,
                        styles=styles[: config.thumbnail_count],
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
                video_mode = "single"
                phase2_prompt = None
                enable_dual_phase_beta = False

                if config.video_dual_phase_beta:
                    video_mode = "dual"
                    enable_dual_phase_beta = True
                    category = product.get("category", "product")
                    phase2_prompt = (
                        "Freeze frame hero shot of a premium "
                        f"{category} on a clean studio background. "
                        "Soft light leaks, slow zoom in, subtle CTA text."
                    )

                video_result = self._video.generate_marketing_video(
                    product=product,
                    strategy=strategy,
                    duration_seconds=config.video_duration,
                    mode=video_mode,
                    phase2_prompt=phase2_prompt,
                    enable_dual_phase_beta=enable_dual_phase_beta,
                )

                if isinstance(video_result, bytes):
                    generated_content.video_bytes = video_result
                else:
                    generated_content.video_url = video_result

            # Step 5: Upload (optional)
            if upload_enabled:
                update_progress(PipelineStep.UPLOAD, "Uploading to GCS...")
                upload_status, upload_errors = self._upload_to_gcs(
                    product=product,
                    config=config,
                    collected_data=collected_data,
                    strategy=strategy,
                    generated_content=generated_content,
                )

            # 완료
            update_progress(PipelineStep.COMPLETED, "파이프라인 완료!")
            duration = time.time() - start_time
            self._last_duration = duration

            log_success(f"파이프라인 실행 완료 (소요 시간: {duration:.2f}초)")
            log_timing("Pipeline Execution", duration * 1000)

            result = PipelineResult(
                success=True,
                product_name=product.get("name", ""),
                config=config,
                collected_data=collected_data,
                strategy=strategy,
                generated_content=generated_content,
                upload_status=upload_status,
                upload_errors=upload_errors,
                duration_seconds=duration,
            )

            # 히스토리 저장
            try:
                save_path = self._history.save_result(result)
                log_info(f"파이프라인 결과 저장 완료: {save_path}")
            except Exception as e:
                logger.error(f"파이프라인 결과 저장 실패: {e}")

            return result

        except Exception as e:
            logger.error(f"파이프라인 실행 실패: {e}")
            update_progress(PipelineStep.FAILED, str(e))
            duration = time.time() - start_time
            self._last_duration = duration

            result = PipelineResult(
                success=False,
                product_name=product.get("name", ""),
                config=config,
                collected_data=collected_data,
                strategy=strategy,
                generated_content=generated_content,
                upload_status=upload_status,
                upload_errors=upload_errors,
                error_message=str(e),
                duration_seconds=duration,
            )

            # 실패 결과도 저장
            try:
                self._history.save_result(result)
            except Exception as e:
                log_error(f"파이프라인 실패 결과 저장 실패: {e}")

            return result

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
            raise PipelineError(
                f"데이터 수집 실패: {e}",
                original_error=e,
            )

    @staticmethod
    def _run_async(coro):
        """새 이벤트 루프에서 비동기 작업 실행"""
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            loop.close()


    def _upload_to_gcs(
        self,
        product: dict,
        config: PipelineConfig,
        collected_data: CollectedData,
        strategy: dict,
        generated_content: GeneratedContent,
    ) -> tuple[UploadStatus, list[str]]:
        """GCS upload (auto bucket creation)."""
        prefix = build_gcs_prefix(product, "pipeline")
        storage = self._storage
        errors: list[str] = []
        total_uploads = 0

        if collected_data:
            total_uploads += 1
            try:
                storage.upload(
                    data=collected_data.model_dump(),
                    path=f"{prefix}/collected_data.json",
                    content_type="application/json",
                )
            except Exception as e:
                log_error(f"GCS collected_data upload failed: {e}")
                errors.append(f"collected_data.json: {e}")

        if strategy:
            total_uploads += 1
            try:
                storage.upload(
                    data=strategy,
                    path=f"{prefix}/strategy.json",
                    content_type="application/json",
                )
            except Exception as e:
                log_error(f"GCS strategy upload failed: {e}")
                errors.append(f"strategy.json: {e}")

        if generated_content.thumbnail_data and not generated_content.multi_thumbnails:
            total_uploads += 1
            try:
                ext = detect_image_ext(generated_content.thumbnail_data)
                thumb_path = f"{prefix}/thumbnail{ext}"
                storage.upload(
                    data=generated_content.thumbnail_data,
                    path=thumb_path,
                    content_type="image/png" if ext == ".png" else "image/jpeg",
                )
                generated_content.thumbnail_url = gcs_url_for(storage, thumb_path)
            except Exception as e:
                log_error(f"GCS thumbnail upload failed: {e}")
                errors.append(f"thumbnail{ext}: {e}")

        if generated_content.multi_thumbnails:
            for idx, item in enumerate(generated_content.multi_thumbnails):
                image_bytes = item.get("image") or item.get("image_bytes")
                if not image_bytes:
                    continue
                total_uploads += 1
                try:
                    ext = detect_image_ext(image_bytes)
                    multi_path = f"{prefix}/thumbnail_{idx + 1}{ext}"
                    storage.upload(
                        data=image_bytes,
                        path=multi_path,
                        content_type="image/png" if ext == ".png" else "image/jpeg",
                    )
                    item["url"] = gcs_url_for(storage, multi_path)
                except Exception as e:
                    log_error(f"GCS thumbnail #{idx + 1} upload failed: {e}")
                    errors.append(f"thumbnail_{idx + 1}{ext}: {e}")

        if generated_content.video_bytes:
            total_uploads += 1
            try:
                ext = detect_video_ext(generated_content.video_bytes)
                video_path = f"{prefix}/video{ext}"
                storage.upload(
                    data=generated_content.video_bytes,
                    path=video_path,
                    content_type="video/mp4" if ext == ".mp4" else "application/octet-stream",
                )
                generated_content.video_url = gcs_url_for(storage, video_path)
            except Exception as e:
                log_error(f"GCS video upload failed: {e}")
                errors.append(f"video{ext}: {e}")

        metadata = {
            "product": product,
            "config": config.model_dump() if hasattr(config, "model_dump") else dict(config),
            "duration_seconds": getattr(self, "_last_duration", None),
            "thumbnail_url": generated_content.thumbnail_url,
            "video_url": generated_content.video_url,
        }
        total_uploads += 1
        try:
            storage.upload(
                data=metadata,
                path=f"{prefix}/metadata.json",
                content_type="application/json",
            )
        except Exception as e:
            log_error(f"GCS metadata upload failed: {e}")
            errors.append(f"metadata.json: {e}")

        if total_uploads == 0:
            return UploadStatus.SKIPPED, []
        if not errors:
            return UploadStatus.SUCCESS, []
        if len(errors) < total_uploads:
            return UploadStatus.PARTIAL, errors
        return UploadStatus.FAILED, errors
