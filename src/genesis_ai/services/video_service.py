"""
비디오 서비스
AI 기반 마케팅 비디오 생성 비즈니스 로직
"""
from typing import Callable, Optional

from ..core.exceptions import VideoGenerationError
from ..infrastructure.clients.veo_client import VeoClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class VideoService:
    """비디오 생성 서비스"""

    def __init__(self, client: VeoClient) -> None:
        self._client = client

    def generate(
        self,
        prompt: str,
        duration_seconds: int = 8,
        resolution: str = "720p",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | str:
        """비디오 생성"""
        logger.info(f"비디오 생성 시작: {duration_seconds}초, {resolution}")

        try:
            result = self._client.generate_video(
                prompt=prompt,
                duration_seconds=duration_seconds,
                resolution=resolution,
                progress_callback=progress_callback,
            )

            if isinstance(result, bytes):
                logger.info(f"비디오 생성 완료: {len(result)} bytes")
            else:
                logger.info(f"비디오 생성 상태: {result[:100]}")

            return result

        except Exception as e:
            logger.error(f"비디오 생성 실패: {e}")
            raise VideoGenerationError(f"비디오 생성 실패: {e}")

    def generate_from_image(
        self,
        image_bytes: bytes,
        prompt: str,
        duration_seconds: int = 8,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """이미지 기반 비디오 생성"""
        logger.info("이미지 기반 비디오 생성 시작")

        try:
            result = self._client.generate_video_from_image(
                image_bytes=image_bytes,
                prompt=prompt,
                duration_seconds=duration_seconds,
                progress_callback=progress_callback,
            )

            if result:
                logger.info(f"이미지 기반 비디오 생성 완료: {len(result)} bytes")

            return result

        except Exception as e:
            logger.error(f"이미지 기반 비디오 생성 실패: {e}")
            raise VideoGenerationError(f"이미지 기반 비디오 생성 실패: {e}")

    def create_marketing_prompt(
        self,
        product: dict,
        insights: dict,
        hook_text: str = "",
    ) -> str:
        """마케팅 비디오 프롬프트 생성"""
        return self._client.generate_marketing_prompt(
            product=product,
            insights=insights,
            hook_text=hook_text,
        )

    def generate_marketing_video(
        self,
        product: dict,
        strategy: dict,
        duration_seconds: int = 8,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | str:
        """마케팅 비디오 생성"""
        logger.info(f"마케팅 비디오 생성 시작: {product.get('name', 'N/A')}")

        # 전략에서 훅 텍스트 추출
        hooks = strategy.get("hook_suggestions", [])
        hook_text = hooks[0] if hooks else f"{product.get('name', '제품')}!"

        # 인사이트 구성
        insights = {
            "hook": hook_text,
            "style": "commercial",
            "mood": "dramatic",
        }

        # 프롬프트 생성
        prompt = self.create_marketing_prompt(product, insights, hook_text)

        # 비디오 생성
        return self.generate(
            prompt=prompt,
            duration_seconds=duration_seconds,
            progress_callback=progress_callback,
        )

    def get_available_motions(self) -> list[str]:
        """사용 가능한 카메라 모션 목록"""
        return self._client.get_available_motions()

    def generate_multi_prompts(
        self,
        product: dict,
        base_hook: str,
        duration_seconds: int = 8,
    ) -> list[dict]:
        """다양한 스타일의 비디오 프롬프트 생성"""
        return self._client.generate_multi_video_prompts(
            product=product,
            base_hook=base_hook,
            duration_seconds=duration_seconds,
        )
