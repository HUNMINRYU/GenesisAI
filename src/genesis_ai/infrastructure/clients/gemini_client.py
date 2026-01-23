"""
Gemini AI 클라이언트
Vertex AI 기반 텍스트/이미지 생성
"""

import json
import re
import time
from typing import Any, Callable, Optional

from ...config.constants import HOOK_TEMPLATES, HOOK_TYPES
from ...core.exceptions import GeminiAPIError
from ...utils.logger import get_logger

logger = get_logger(__name__)


class GeminiClient:
    """Gemini AI 클라이언트"""

    def __init__(
        self,
        project_id: str,
        location: str,
        text_model: str = "gemini-3-pro-preview",
        image_model: str = "gemini-3-pro-image-preview",
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._text_model = text_model
        self._image_model = image_model
        self._client = None

    def _get_client(self):
        """Gemini 클라이언트 인스턴스 반환 (지연 초기화)"""
        if self._client is None:
            from google import genai

            self._client = genai.Client(
                vertexai=True,
                project=self._project_id,
                location=self._location,
            )
        return self._client

    def is_configured(self) -> bool:
        """설정 확인"""
        return bool(self._project_id and self._location)

    def health_check(self) -> bool:
        """API 연결 상태 확인"""
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        use_grounding: bool = False,
    ) -> str:
        """텍스트 생성"""
        try:
            from google.genai import types

            client = self._get_client()

            config = types.GenerateContentConfig(temperature=temperature)

            if use_grounding:
                config.tools = [types.Tool(google_search=types.GoogleSearch())]

            response = client.models.generate_content(
                model=self._text_model,
                contents=prompt,
                config=config,
            )

            return response.text

        except Exception as e:
            logger.error(f"텍스트 생성 실패: {e}")
            raise GeminiAPIError(f"텍스트 생성 실패: {e}")

    def generate_image(
        self,
        prompt: str,
        aspect_ratio: str = "16:9",
    ) -> bytes | None:
        """이미지 생성 (genesis_kr/v3 방식: generate_content + response_modalities)"""
        try:
            import base64
            from google.genai.types import GenerateContentConfig, Modality

            client = self._get_client()

            # v3와 동일: generate_content + response_modalities 사용
            response = client.models.generate_content(
                model=self._image_model,
                contents=prompt,
                config=GenerateContentConfig(
                    response_modalities=[Modality.TEXT, Modality.IMAGE],
                ),
            )

            # 이미지가 포함된 응답 처리
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        img_data = part.inline_data.data
                        if isinstance(img_data, str):
                            img_data = base64.b64decode(img_data)
                        logger.info(f"이미지 생성 완료: {len(img_data):,} bytes")
                        return img_data

            return None

        except Exception as e:
            logger.error(f"이미지 생성 실패: {e}")
            raise GeminiAPIError(f"이미지 생성 실패: {e}")

    def analyze_marketing_data(
        self,
        youtube_data: dict,
        naver_data: dict,
        product_name: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        use_search_grounding: bool = True,
    ) -> dict[str, Any]:
        """마케팅 데이터 분석"""
        logger.info(f"마케팅 분석 시작: {product_name}")

        try:
            from google.genai import types

            client = self._get_client()

            if progress_callback:
                progress_callback("마케팅 데이터 분석 중...", 20)

            analysis_prompt = f"""
당신은 전문 마케팅 분석가입니다. 다음 데이터를 분석하여 마케팅 인사이트를 제공해주세요.

## 분석 대상 제품
제품명: {product_name}

## YouTube 데이터
{json.dumps(youtube_data, ensure_ascii=False, indent=2) if youtube_data else "데이터 없음"}

## 네이버 쇼핑 데이터
{json.dumps(naver_data, ensure_ascii=False, indent=2) if naver_data else "데이터 없음"}

## 분석 요청
다음 형식으로 분석 결과를 JSON으로 반환해주세요:

{{
    "target_audience": {{
        "primary": "주요 타겟 고객층",
        "secondary": "2차 타겟 고객층",
        "pain_points": ["고객 페인 포인트 1", "페인 포인트 2", "페인 포인트 3"],
        "desires": ["고객이 원하는 것 1", "원하는 것 2", "원하는 것 3"]
    }},
    "competitor_analysis": {{
        "price_range": "가격대 분석",
        "key_features": ["주요 경쟁 기능 1", "기능 2", "기능 3"],
        "differentiators": ["차별화 포인트 1", "포인트 2"]
    }},
    "content_strategy": {{
        "trending_topics": ["인기 주제 1", "주제 2", "주제 3"],
        "content_types": ["효과적인 콘텐츠 유형 1", "유형 2"],
        "posting_tips": ["포스팅 팁 1", "팁 2"]
    }},
    "hook_suggestions": [
        "훅 문구 제안 1",
        "훅 문구 제안 2",
        "훅 문구 제안 3",
        "훅 문구 제안 4",
        "훅 문구 제안 5"
    ],
    "keywords": ["키워드 1", "키워드 2", "키워드 3", "키워드 4", "키워드 5"],
    "summary": "전체 분석 요약 (2-3문장)"
}}
"""

            if progress_callback:
                progress_callback("AI 분석 진행 중...", 50)

            config = types.GenerateContentConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )

            if use_search_grounding:
                config.tools = [types.Tool(google_search=types.GoogleSearch())]

            response = client.models.generate_content(
                model=self._text_model,
                contents=analysis_prompt,
                config=config,
            )

            if progress_callback:
                progress_callback("분석 결과 처리 중...", 80)

            result = self._validate_json_output(response.text)

            logger.info("마케팅 분석 완료")

            if progress_callback:
                progress_callback("분석 완료!", 100)

            return result

        except Exception as e:
            logger.error(f"마케팅 분석 실패: {e}")
            if progress_callback:
                progress_callback(f"오류: {e}", 0)
            return {"error": str(e)}

    def generate_marketing_strategy(
        self,
        collected_data: dict,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> dict[str, Any]:
        """마케팅 전략 생성"""
        product = collected_data.get("product", {})
        product_name = product.get("name", "제품")

        youtube_data = collected_data.get("youtube_data", {})
        naver_data = collected_data.get("naver_data", {})

        return self.analyze_marketing_data(
            youtube_data=youtube_data,
            naver_data=naver_data,
            product_name=product_name,
            progress_callback=progress_callback,
            use_search_grounding=True,
        )

    def _build_image_prompt(
        self,
        product: dict,
        hook_text: str,
        style: str = "드라마틱",
        color_scheme: str = "블루 그라디언트",
        layout: str = "중앙 집중형",
    ) -> str:
        """마케팅 이미지 생성 프롬프트 빌드"""
        product_name = product.get("name", "제품")
        product_category = product.get("category", "일반")

        return f"""
Create a stunning marketing thumbnail image for e-commerce.

PRODUCT: {product_name}
CATEGORY: {product_category}
HOOK TEXT: "{hook_text}"

STYLE REQUIREMENTS:
- Visual Style: {style} with high-end commercial quality
- Color Scheme: {color_scheme}
- Layout: {layout}

COMPOSITION:
- Professional product photography aesthetic
- Clean, uncluttered background
- Dramatic lighting with soft shadows
- Focus on product as hero element

TEXT OVERLAY:
- Include hook text "{hook_text}" prominently
- Use modern, bold typography
- Ensure high contrast for readability

TECHNICAL:
- High resolution, sharp details
- Aspect ratio 16:9
- Photorealistic quality
- No watermarks or logos

MOOD:
- Premium, trustworthy, professional
- Appeals to online shoppers
- Creates urgency and desire
""".strip()

    def generate_thumbnail(
        self,
        product: dict,
        hook_text: str,
        style: str = "드라마틱",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """마케팅 썸네일 생성"""
        logger.info(f"썸네일 생성 시작: {product.get('name', 'N/A')}")

        try:
            if progress_callback:
                progress_callback("프롬프트 구성 중...", 10)

            prompt = self._build_image_prompt(product, hook_text, style)

            if progress_callback:
                progress_callback("이미지 생성 중...", 30)

            image_data = self.generate_image(prompt, aspect_ratio="16:9")

            if progress_callback:
                progress_callback("이미지 처리 중...", 80)

            if image_data:
                logger.info(f"썸네일 생성 완료: {len(image_data)} bytes")
                if progress_callback:
                    progress_callback("썸네일 준비 완료!", 100)
                return image_data

            logger.error("생성된 이미지 없음")
            return None

        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            if progress_callback:
                progress_callback(f"오류: {e}", 0)
            return None

    def generate_multiple_thumbnails(
        self,
        product: dict,
        hook_texts: list[str],
        styles: list[str] | None = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """다중 썸네일 생성"""
        logger.info(f"다중 썸네일 생성 시작: {len(hook_texts)}개")

        if styles is None:
            styles = ["드라마틱", "미니멀", "모던"]

        results = []
        total = len(hook_texts)

        for i, hook_text in enumerate(hook_texts):
            style = styles[i % len(styles)]

            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(f"썸네일 {i + 1}/{total} 생성 중...", progress)

            image = self.generate_thumbnail(product, hook_text, style)

            if image:
                results.append(
                    {
                        "image": image,
                        "hook_text": hook_text,
                        "style": style,
                    }
                )

        logger.info(f"다중 썸네일 생성 완료: {len(results)}/{total}")

        if progress_callback:
            progress_callback("모든 썸네일 생성 완료!", 100)

        return results

    def generate_hook_texts(
        self,
        product_name: str,
        hook_types: list[str] | None = None,
        count: int = 5,
        custom_params: dict | None = None,
    ) -> list[dict]:
        """심리학 기반 훅 텍스트 생성"""
        if hook_types is None:
            hook_types = HOOK_TYPES

        params = {
            "product": product_name,
            "count": "10만",
            "discount": "50",
            "benefit": "효과",
            **(custom_params or {}),
        }

        hooks = []
        for hook_type in hook_types:
            if hook_type in HOOK_TEMPLATES:
                for template in HOOK_TEMPLATES[hook_type]:
                    try:
                        hook = template.format(**params)
                        hooks.append({"text": hook, "type": hook_type})
                    except KeyError:
                        continue

        # 중복 제거 및 개수 제한
        seen = set()
        unique_hooks = []
        for h in hooks:
            if h["text"] not in seen:
                seen.add(h["text"])
                unique_hooks.append(h)
                if len(unique_hooks) >= count:
                    break

        return unique_hooks

    def _validate_json_output(
        self,
        text: str,
        required_fields: list[str] | None = None,
    ) -> dict:
        """LLM 출력 JSON 검증"""
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", text)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                except json.JSONDecodeError:
                    return {"error": "JSON 파싱 실패", "raw_text": text[:500]}
            else:
                return {"error": "JSON을 찾을 수 없음", "raw_text": text[:500]}

        if required_fields:
            missing = [f for f in required_fields if f not in result]
            if missing:
                result["_validation_warning"] = f"누락된 필드: {missing}"

        return result

    def retry_with_backoff(
        self,
        func: Callable,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
    ):
        """지수 백오프 재시도"""
        last_error = None

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = min(base_delay * (2**attempt), max_delay)
                    logger.info(
                        f"재시도 {attempt + 1}/{max_retries} ({delay:.1f}초 후)"
                    )
                    time.sleep(delay)

        raise last_error  # type: ignore
