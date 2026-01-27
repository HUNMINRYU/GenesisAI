"""
Social Media Post Generation Service
채널별(인스타그램, 트위터, 블로그 등) 마케팅 문구 생성
"""
from typing import Any

from ..core.interfaces.ai_service import IMarketingAIService
from ..utils.logger import get_logger, log_step, log_success

logger = get_logger(__name__)

class SocialMediaService:
    def __init__(self, gemini_client: IMarketingAIService):
        self._gemini = gemini_client

    async def generate_posts(
        self,
        product: dict,
        strategy: dict,
        top_insights: list[dict] = None,
        platforms: list[str] = None,
    ) -> dict[str, Any]:
        log_step("SNS 포스팅 생성", "시작", f"플랫폼: {platforms}")

        if not platforms:
            platforms = ["instagram", "twitter", "blog"]

        product_name = product.get("name", "제품")
        summary = strategy.get("summary", "")

        import json
        insights_text = json.dumps(top_insights, ensure_ascii=False, indent=2) if top_insights else "N/A"

        prompt = f"""
당신은 소셜 미디어 마케팅 전문가입니다. 다음 제품 정보를 바탕으로 각 채널별 맞춤형 포스팅 문구를 생성해주세요.

## 제품 정보
- 제품명: {product_name}
- 핵심 전략: {summary}

## X-Algorithm 핵심 인사이트 (고객의 실제 목소리)
{insights_text}

## 요청 사항
1. 인스타그램(Instagram): 비주얼 중심, 감성적인 문구, 해시태그 포함
2. 트위터(X): 짧고 강렬한 훅, 바이럴 유도, 핵심 키워드 중심
3. 블로그(Blog): 상세한 정보 전달, 신뢰감 있는 톤, 구조화된 설명

반드시 다음 JSON 형식으로 응답하세요:
{{
    "instagram": {{
        "caption": "인스타그램 문구",
        "hashtags": ["#태그1", "#태그2"]
    }},
    "twitter": {{
        "content": "트위터 문구"
    }},
    "blog": {{
        "title": "블로그 제목",
        "content": "블로그 요약 본문"
    }}
}}
"""
        try:
            # 인터페이스 타입 힌트에도 불구하고 실제 인스턴스가 generate_content_async를 가지고 있는지 확인
            if hasattr(self._gemini, "generate_content_async"):
                response_text = await self._gemini.generate_content_async(prompt)
            else:
                # 동기 방식 fallback (테스트용)
                response_text = self._gemini.generate_text(prompt)

            # JSON 파싱
            cleaned_text = response_text.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned_text)

            log_success("SNS 포스팅 생성 완료")
            return result
        except Exception as e:
            logger.error(f"SNS 포스팅 생성 실패: {e}")
            return {
                "error": str(e),
                "instagram": {"caption": "생성 실패", "hashtags": []},
                "twitter": {"content": "생성 실패"},
                "blog": {"title": "생성 실패", "content": "생성 실패"}
            }
