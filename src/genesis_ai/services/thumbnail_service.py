"""
썸네일 서비스
AI 기반 마케팅 썸네일 생성 비즈니스 로직
"""
from typing import Callable, Optional

from ..core.exceptions import ThumbnailGenerationError
from ..infrastructure.clients.gemini_client import GeminiClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ThumbnailService:
    """썸네일 생성 서비스"""

    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    def generate(
        self,
        product: dict,
        hook_text: str,
        style: str = "드라마틱",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """썸네일 생성"""
        logger.info(f"썸네일 생성 시작: {product.get('name', 'N/A')}")

        try:
            result = self._client.generate_thumbnail(
                product=product,
                hook_text=hook_text,
                style=style,
                progress_callback=progress_callback,
            )

            if result:
                logger.info(f"썸네일 생성 완료: {len(result)} bytes")
                return result

            raise ThumbnailGenerationError("썸네일 생성 결과가 없습니다")

        except ThumbnailGenerationError:
            raise
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            raise ThumbnailGenerationError(f"썸네일 생성 실패: {e}")

    def generate_multiple(
        self,
        product: dict,
        hook_texts: list[str],
        styles: list[str] | None = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """다중 썸네일 생성"""
        logger.info(f"다중 썸네일 생성 시작: {len(hook_texts)}개")

        try:
            results = self._client.generate_multiple_thumbnails(
                product=product,
                hook_texts=hook_texts,
                styles=styles,
                progress_callback=progress_callback,
            )

            logger.info(f"다중 썸네일 생성 완료: {len(results)}개")
            return results

        except Exception as e:
            logger.error(f"다중 썸네일 생성 실패: {e}")
            raise ThumbnailGenerationError(f"다중 썸네일 생성 실패: {e}")

    def generate_from_strategy(
        self,
        product: dict,
        strategy: dict,
        count: int = 3,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """전략 기반 썸네일 생성"""
        # 전략에서 훅 텍스트 추출
        hooks = strategy.get("hook_suggestions", [])
        if not hooks:
            hooks = [f"{product.get('name', '제품')} 지금 바로!"]

        hook_texts = hooks[:count]

        return self.generate_multiple(
            product=product,
            hook_texts=hook_texts,
            progress_callback=progress_callback,
        )
