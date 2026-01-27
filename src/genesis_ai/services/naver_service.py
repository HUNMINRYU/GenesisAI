"""
네이버 서비스
네이버 쇼핑 데이터 수집 비즈니스 로직
"""

from typing import Callable, Optional

from ..core.exceptions import DataCollectionError
from ..core.interfaces.api_client import INaverClient
from ..utils.cache import cached
from ..utils.logger import (
    log_api_end,
    log_api_start,
    log_data,
    log_error,
    log_step,
    log_success,
)


class NaverService:
    """네이버 쇼핑 데이터 수집 서비스"""

    def __init__(self, client: INaverClient) -> None:
        self._client = client

    @cached(ttl=600, cache_key_prefix="naver")  # 10분 캐시
    def search_products(self, query: str, max_results: int = 10) -> list[dict]:
        """상품 검색 (캐시 적용: 동일 검색어는 10분간 재사용)"""
        log_api_start("Naver Shopping Search", f"Query: {query}, Max: {max_results}")

        try:
            results = self._client.search_shopping(query, max_results)
            log_api_end("Naver Shopping Search", items=len(results))
            return results
        except Exception as e:
            log_error(f"네이버 검색 실패: {e}")
            raise DataCollectionError(
                "네이버 검색 실패",
                original_error=e,
            )

    def analyze_competitors(self, products: list[dict]) -> dict:
        """경쟁사 분석"""
        return self._client.analyze_competitors(products)

    def collect_product_data(
        self,
        product: dict,
        max_results: int = 10,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict:
        """제품 기반 네이버 쇼핑 데이터 수집"""
        p_name = product.get("name", "N/A")
        log_step("네이버 데이터 수집", "시작", f"제품: {p_name}")

        try:
            if progress_callback:
                progress_callback("네이버 쇼핑 검색 중...", 10)

            # 제품명으로 검색
            products = self.search_products(product["name"], max_results)

            if progress_callback:
                progress_callback("경쟁사 분석 중...", 50)

            # 경쟁사 분석
            competitor_stats = self.analyze_competitors(products)

            if progress_callback:
                progress_callback("네이버 데이터 수집 완료", 100)

            result = {
                "product": product,
                "products": products,
                "competitor_stats": competitor_stats,
                "total_count": len(products),
            }

            log_success(f"네이버 쇼핑 데이터 수집 완료 ({len(products)}개 상품)")
            log_data("Products", len(products), "Naver")
            return result

        except Exception as e:
            log_error(f"네이버 쇼핑 데이터 수집 실패: {e}")
            raise DataCollectionError(
                f"네이버 쇼핑 데이터 수집 실패: {e}",
                original_error=e,
            )

    def get_price_summary(self, products: list[dict]) -> str:
        """가격 요약 문자열 생성"""
        if not products:
            return "데이터 없음"

        stats = self.analyze_competitors(products)
        return f"최저 {stats['min_price']:,}원 ~ 최고 {stats['max_price']:,}원 (평균 {stats['avg_price']:,}원)"
