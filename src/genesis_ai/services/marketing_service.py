"""
마케팅 서비스
AI 기반 마케팅 전략 생성 비즈니스 로직
"""
from typing import Any, Callable, Optional

from ..core.exceptions import StrategyGenerationError
from ..core.models import MarketingStrategy
from ..infrastructure.clients.gemini_client import GeminiClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class MarketingService:
    """마케팅 전략 생성 서비스"""

    def __init__(self, client: GeminiClient) -> None:
        self._client = client

    def analyze_data(
        self,
        youtube_data: dict,
        naver_data: dict,
        product_name: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        use_grounding: bool = True,
    ) -> dict[str, Any]:
        """마케팅 데이터 분석"""
        logger.info(f"마케팅 데이터 분석 시작: {product_name}")

        try:
            result = self._client.analyze_marketing_data(
                youtube_data=youtube_data,
                naver_data=naver_data,
                product_name=product_name,
                progress_callback=progress_callback,
                use_search_grounding=use_grounding,
            )

            if "error" in result:
                raise StrategyGenerationError(result["error"])

            logger.info("마케팅 데이터 분석 완료")
            return result

        except StrategyGenerationError:
            raise
        except Exception as e:
            logger.error(f"마케팅 데이터 분석 실패: {e}")
            raise StrategyGenerationError(f"마케팅 데이터 분석 실패: {e}")

    def generate_strategy(
        self,
        collected_data: dict,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict[str, Any]:
        """마케팅 전략 생성"""
        logger.info("마케팅 전략 생성 시작")

        try:
            result = self._client.generate_marketing_strategy(
                collected_data=collected_data,
                progress_callback=progress_callback,
            )

            if "error" in result:
                raise StrategyGenerationError(result["error"])

            logger.info("마케팅 전략 생성 완료")
            return result

        except StrategyGenerationError:
            raise
        except Exception as e:
            logger.error(f"마케팅 전략 생성 실패: {e}")
            raise StrategyGenerationError(f"마케팅 전략 생성 실패: {e}")

    def generate_hooks(
        self,
        product_name: str,
        hook_types: list[str] | None = None,
        count: int = 5,
    ) -> list[dict]:
        """훅 텍스트 생성"""
        return self._client.generate_hook_texts(
            product_name=product_name,
            hook_types=hook_types,
            count=count,
        )

    def extract_key_insights(self, strategy: dict) -> dict:
        """전략에서 핵심 인사이트 추출"""
        return {
            "target_audience": strategy.get("target_audience", {}),
            "hooks": strategy.get("hook_suggestions", [])[:3],
            "keywords": strategy.get("keywords", [])[:5],
            "summary": strategy.get("summary", ""),
        }
