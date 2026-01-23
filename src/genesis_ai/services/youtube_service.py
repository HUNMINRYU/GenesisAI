"""
YouTube 서비스
YouTube 데이터 수집 비즈니스 로직
"""
from typing import Callable, Optional

from ..core.exceptions import DataCollectionError
from ..core.models import YouTubeSearchResult
from ..infrastructure.clients.youtube_client import YouTubeClient
from ..utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeService:
    """YouTube 데이터 수집 서비스"""

    def __init__(self, client: YouTubeClient) -> None:
        self._client = client

    def search_videos(self, query: str, max_results: int = 3) -> list[dict]:
        """비디오 검색"""
        return self._client.search(query, max_results)

    def get_video_details(self, video_id: str) -> dict | None:
        """비디오 상세 정보"""
        return self._client.get_video_details(video_id)

    def get_comments(self, video_id: str, max_results: int = 20) -> list[dict]:
        """비디오 댓글"""
        return self._client.get_video_comments(video_id, max_results)

    def get_transcript(self, video_id: str) -> str | None:
        """비디오 자막"""
        return self._client.get_transcript(video_id)

    def collect_product_data(
        self,
        product: dict,
        max_results: int = 5,
        include_comments: bool = True,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """제품 기반 YouTube 데이터 수집"""
        logger.info(f"YouTube 데이터 수집 시작: {product.get('name', 'N/A')}")

        try:
            if progress_callback:
                progress_callback("YouTube 데이터 수집 중...", 10)

            data = self._client.collect_video_data(
                product=product,
                max_results=max_results,
                include_comments=include_comments,
            )

            if progress_callback:
                progress_callback("YouTube 데이터 수집 완료", 100)

            logger.info(f"YouTube 데이터 수집 완료: {len(data.get('videos', []))}개 비디오")
            return data

        except Exception as e:
            logger.error(f"YouTube 데이터 수집 실패: {e}")
            raise DataCollectionError(f"YouTube 데이터 수집 실패: {e}")

    def analyze_comments(self, comments: list[dict]) -> dict:
        """댓글 분석 (페인/게인 포인트)"""
        pain_points = self._client._extract_pain_points(comments)
        gain_points = self._client._extract_gain_points(comments)

        return {
            "total_comments": len(comments),
            "pain_points": pain_points,
            "gain_points": gain_points,
            "pain_count": len(pain_points),
            "gain_count": len(gain_points),
        }
