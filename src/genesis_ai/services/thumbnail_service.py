"""
썸네일 서비스
AI 기반 마케팅 썸네일 생성 비즈니스 로직
"""

from dataclasses import dataclass, field
from typing import Callable, Optional

from ..core.exceptions import ThumbnailGenerationError
from ..core.interfaces.ai_service import IMarketingAIService
from ..utils.logger import get_logger

logger = get_logger(__name__)


# === 썸네일 스타일 프리셋 ===
THUMBNAIL_STYLES = {
    "dramatic": {
        "name": "드라마틱",
        "prompt_modifier": "dramatic lighting, high contrast, cinematic mood, dark background with spotlight",
        "colors": "deep shadows, golden highlights",
    },
    "neobrutalism": {
        "name": "네오브루탈리즘",
        "prompt_modifier": "neo-brutalism design style, bold black outlines, solid bright colors, drop shadows, chunky geometric shapes, playful yet bold",
        "colors": "vibrant yellow, hot pink, electric blue, lime green on white or beige background",
    },
    "minimal": {
        "name": "미니멀",
        "prompt_modifier": "clean minimalist design, lots of white space, simple composition, modern aesthetic",
        "colors": "monochrome with one accent color",
    },
    "vibrant": {
        "name": "비비드",
        "prompt_modifier": "vibrant saturated colors, energetic composition, dynamic angles, pop art influence",
        "colors": "bright neon colors, gradient overlays",
    },
    "professional": {
        "name": "프로페셔널",
        "prompt_modifier": "professional corporate style, clean layout, trustworthy appearance, subtle gradients",
        "colors": "navy blue, white, gold accents",
    },
    "photorealistic": {
        "name": "실사형",
        "prompt_modifier": "photorealistic high-quality photograph, professional photography, sharp details, natural colors",
        "colors": "true-to-life colors with professional color grading",
    },
}


# === Shot Type Presets (이미지 프롬프트 가이드 기반) ===
SHOT_TYPES = {
    "portrait": {
        "name": "Portrait",
        "name_ko": "인물샷",
        "prompt": "portrait shot focusing on face and expression",
    },
    "product": {
        "name": "Product",
        "name_ko": "제품샷",
        "prompt": "product photography with clean background",
    },
    "hero": {
        "name": "Hero",
        "name_ko": "히어로샷",
        "prompt": "dramatic hero shot with dynamic composition",
    },
    "lifestyle": {
        "name": "Lifestyle",
        "name_ko": "라이프스타일",
        "prompt": "lifestyle photography showing product in use",
    },
    "flat_lay": {
        "name": "Flat Lay",
        "name_ko": "플랫레이",
        "prompt": "top-down flat lay arrangement",
    },
    "macro": {
        "name": "Macro",
        "name_ko": "매크로",
        "prompt": "extreme close-up macro shot showing fine details",
    },
    "action": {
        "name": "Action",
        "name_ko": "액션샷",
        "prompt": "dynamic action shot with motion blur",
    },
    "environmental": {
        "name": "Environmental",
        "name_ko": "환경샷",
        "prompt": "wide environmental shot with context",
    },
}

# === Lighting Presets ===
LIGHTING_PRESETS = {
    "golden_hour": {
        "name": "Golden Hour",
        "name_ko": "골든아워",
        "prompt": "warm golden hour sunlight with soft shadows",
    },
    "studio": {
        "name": "Studio",
        "name_ko": "스튜디오",
        "prompt": "professional studio lighting with key, fill and rim lights",
    },
    "dramatic": {
        "name": "Dramatic",
        "name_ko": "드라마틱",
        "prompt": "high contrast dramatic chiaroscuro lighting",
    },
    "natural": {
        "name": "Natural",
        "name_ko": "자연광",
        "prompt": "soft natural window light",
    },
    "neon": {
        "name": "Neon",
        "name_ko": "네온",
        "prompt": "vibrant neon glow with colorful reflections",
    },
    "backlit": {
        "name": "Backlit",
        "name_ko": "역광",
        "prompt": "silhouette backlit with rim light",
    },
    "soft_box": {
        "name": "Soft Box",
        "name_ko": "소프트박스",
        "prompt": "even soft box studio lighting",
    },
    "ring_light": {
        "name": "Ring Light",
        "name_ko": "링라이트",
        "prompt": "beauty ring light with catchlights in eyes",
    },
}

# === Lens/Camera Presets ===
LENS_PRESETS = {
    "portrait_85mm": {
        "name": "85mm Portrait",
        "name_ko": "85mm 인물",
        "prompt": "shot with 85mm portrait lens, shallow depth of field, creamy bokeh",
    },
    "wide_24mm": {
        "name": "24mm Wide",
        "name_ko": "24mm 광각",
        "prompt": "captured with 24mm wide-angle lens, dramatic perspective",
    },
    "macro_100mm": {
        "name": "100mm Macro",
        "name_ko": "100mm 매크로",
        "prompt": "extreme close-up with 100mm macro lens, ultra-sharp details",
    },
    "telephoto": {
        "name": "Telephoto",
        "name_ko": "망원",
        "prompt": "telephoto compression, subject isolation",
    },
    "fisheye": {
        "name": "Fisheye",
        "name_ko": "어안",
        "prompt": "fisheye lens with curved distortion",
    },
    "tilt_shift": {
        "name": "Tilt-Shift",
        "name_ko": "틸트시프트",
        "prompt": "tilt-shift lens for miniature effect",
    },
    "standard_50mm": {
        "name": "50mm Standard",
        "name_ko": "50mm 표준",
        "prompt": "natural 50mm standard lens perspective",
    },
}

# === 텍스트 오버레이 가이드 ===
TEXT_OVERLAY_GUIDE = {
    "position": {
        "top": "제목/훅 텍스트 - 상단 1/3",
        "center": "핵심 메시지 - 중앙",
        "bottom": "CTA/부가정보 - 하단",
    },
    "font_style": {
        "impact": "볼드 산세리프, 강렬한 훅용",
        "elegant": "세리프, 고급 제품용",
        "playful": "손글씨체, 친근한 톤용",
    },
    "best_practices": [
        "텍스트는 5단어 이내",
        "배경과 대비되는 색상",
        "그림자/외곽선으로 가독성 확보",
        "얼굴과 겹치지 않게 배치",
    ],
}


@dataclass
class PhotorealisticPromptBuilder:
    """
    실사형 이미지 프롬프트 빌더
    Google AI 이미지 프롬프트 가이드 기반
    """

    # 필수 요소
    subject: str = ""
    action: str = ""

    # 촬영 설정
    shot_type: str = "product"
    environment: str = ""
    lighting: str = "natural"
    lens: str = "standard_50mm"

    # 분위기/스타일
    mood: str = ""
    color_grading: str = ""

    # 추가 세부사항
    details: list[str] = field(default_factory=list)
    aspect_ratio: str = "16:9"

    def build(self) -> str:
        """
        실사형 프롬프트 생성
        템플릿: A photorealistic [shot_type] of [subject], [action].
                Set in [environment]. Illuminated by [lighting].
                Captured with [lens]. [mood] atmosphere. [aspect_ratio].
        """
        parts = []

        # Shot type + Subject
        shot_prompt = SHOT_TYPES.get(self.shot_type, {}).get("prompt", "photograph")
        subject_line = f"A photorealistic {shot_prompt} of {self.subject}"
        if self.action:
            subject_line += f", {self.action}"
        parts.append(subject_line + ".")

        # Environment
        if self.environment:
            parts.append(f"Set in {self.environment}.")

        # Lighting
        light_prompt = LIGHTING_PRESETS.get(self.lighting, {}).get(
            "prompt", "natural lighting"
        )
        parts.append(f"Illuminated by {light_prompt}.")

        # Lens
        lens_prompt = LENS_PRESETS.get(self.lens, {}).get("prompt", "standard lens")
        parts.append(f"Captured with {lens_prompt}.")

        # Mood
        if self.mood:
            parts.append(f"{self.mood} atmosphere.")

        # Color grading
        if self.color_grading:
            parts.append(f"Color grading: {self.color_grading}.")

        # Details
        if self.details:
            details_text = ", ".join(self.details)
            parts.append(f"Emphasizing {details_text}.")

        # Aspect ratio
        parts.append(f"{self.aspect_ratio} format.")

        return " ".join(parts)

    def for_youtube_thumbnail(self) -> "PhotorealisticPromptBuilder":
        """YouTube 썸네일 최적화 설정"""
        self.aspect_ratio = "16:9"
        self.shot_type = "hero"
        self.lighting = "dramatic"
        self.details.extend(["eye-catching composition", "bold visual impact"])
        return self

    def for_product_shot(self, product_name: str) -> "PhotorealisticPromptBuilder":
        """제품 촬영 설정"""
        self.subject = product_name
        self.shot_type = "product"
        self.environment = "clean studio with seamless white background"
        self.lighting = "soft_box"
        self.lens = "standard_50mm"
        return self

    def for_lifestyle(self, product_name: str) -> "PhotorealisticPromptBuilder":
        """라이프스타일 촬영 설정"""
        self.subject = product_name
        self.shot_type = "lifestyle"
        self.lighting = "golden_hour"
        self.mood = "warm and inviting"
        return self

    @staticmethod
    def get_shot_types() -> list[dict]:
        """사용 가능한 샷 타입 목록"""
        return [
            {"key": key, "name": val["name"], "name_ko": val["name_ko"]}
            for key, val in SHOT_TYPES.items()
        ]

    @staticmethod
    def get_lighting_presets() -> list[dict]:
        """사용 가능한 조명 프리셋 목록"""
        return [
            {"key": key, "name": val["name"], "name_ko": val["name_ko"]}
            for key, val in LIGHTING_PRESETS.items()
        ]

    @staticmethod
    def get_lens_presets() -> list[dict]:
        """사용 가능한 렌즈 프리셋 목록"""
        return [
            {"key": key, "name": val["name"], "name_ko": val["name_ko"]}
            for key, val in LENS_PRESETS.items()
        ]


class ThumbnailService:
    """썸네일 생성 서비스"""

    def __init__(self, client: IMarketingAIService) -> None:
        self._client = client

    def get_available_styles(self) -> list[dict]:
        """사용 가능한 스타일 목록 반환"""
        return [
            {
                "key": key,
                "name": style["name"],
                "description": style["prompt_modifier"][:50] + "...",
            }
            for key, style in THUMBNAIL_STYLES.items()
        ]

    def generate(
        self,
        product: dict,
        hook_text: str,
        style: str = "dramatic",
        include_text_overlay: bool = False,
        accent_color: Optional[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """
        썸네일 생성

        Args:
            product: 제품 정보
            hook_text: 후킹 문구
            style: 스타일 키
            include_text_overlay: 텍스트 오버레이 포함 여부
            accent_color: 강조 색상
            progress_callback: 진행 콜백
        """
        logger.info(
            f"Thumbnail generate start: {product.get('name', 'N/A')} (style={style})"
        )

        try:
            prompt = self._build_thumbnail_prompt(
                product=product,
                hook_text=hook_text,
                style=style,
                include_text_overlay=include_text_overlay,
                accent_color=accent_color,
            )
            result = self._client.generate_image(prompt=prompt, aspect_ratio="9:16")

            if result:
                logger.info(f"Thumbnail generate done: {len(result)} bytes")
                return result

            raise ThumbnailGenerationError("썸네일 생성 결과가 없습니다.")

        except ThumbnailGenerationError:
            raise
        except Exception as e:
            logger.error(f"썸네일 생성 실패: {e}")
            raise ThumbnailGenerationError(
                f"썸네일 생성 실패: {e}",
                original_error=e,
            )

    def generate_neobrutalism(
        self,
        product: dict,
        hook_text: str,
        accent_color: str = "yellow",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """
        네오브루탈리즘 스타일 썸네일 생성

        Args:
            product: 제품 정보
            hook_text: 후킹 문구
            accent_color: 강조 색상
            progress_callback: 진행 콜백
        """
        return self.generate(
            product=product,
            hook_text=hook_text,
            style="neobrutalism",
            include_text_overlay=True,
            accent_color=accent_color,
            progress_callback=progress_callback,
        )

    def generate_multiple(
        self,
        product: dict,
        hook_texts: list[str],
        styles: list[str] | None = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """여러 스타일 썸네일 일괄 생성"""
        logger.info(f"Thumbnail batch start: {len(hook_texts)} items")

        if styles is None:
            styles = ["dramatic"] * len(hook_texts)

        results = []
        total = len(hook_texts) if hook_texts else 1

        for i, hook_text in enumerate(hook_texts):
            style_key = styles[i % len(styles)]
            if progress_callback:
                progress = int((i / total) * 100)
                progress_callback(f"썸네일 {i + 1}/{total} 생성 중...", progress)

            image = self.generate(
                product=product,
                hook_text=hook_text,
                style=style_key,
                include_text_overlay=True,
            )
            if image:
                results.append(
                    {
                        "image": image,
                        "hook_text": hook_text,
                        "style": style_key,
                        "style_name": THUMBNAIL_STYLES.get(style_key, {}).get("name", style_key),
                    }
                )

        if progress_callback:
            progress_callback("모든 썸네일 생성 완료!", 100)

        logger.info(f"Thumbnail batch done: {len(results)} items")
        return results

    def _build_thumbnail_prompt(
        self,
        product: dict,
        hook_text: str,
        style: str,
        include_text_overlay: bool,
        accent_color: Optional[str],
    ) -> str:
        product_name = product.get("name", "Product")
        product_category = product.get("category", "Product category")
        benefit = product.get("benefit", "key benefit")

        text_block = ""
        if include_text_overlay:
            text_block = (
                f'Include the text "{hook_text}" in a bold, high-contrast sans-serif font. '
                "Ensure readability at thumbnail size."
            )

        if style in ("photorealistic", "professional"):
            return (
                "{\n"
                '  "model": "nano-banana",\n'
                f'  "prompt": "Create a photorealistic product-focused YouTube thumbnail of {product_name} '
                f'({product_category}) that highlights the benefit: {benefit}. Use clean studio lighting, '
                'a modern commercial mood, sharp textures, and a centered hero composition. Match realistic '
                'scale and perspective with premium clarity and natural contrast. '
                f'{text_block}",\n'
                '  "ratio": "9:16",\n'
                '  "upscale": "Upscale photos to high resolution x2",\n'
                '  "settings": "--no text --no logo --no watermark --no captions --no artifacts --ar 9:16"\n'
                "}"
            ).strip()

        if style == "minimal":
            return (
                "{\n"
                '  "model": "nano-banana",\n'
                f'  "prompt": "Design a minimalist YouTube thumbnail for {product_name} with generous '
                'negative space, an off-white background, and a single accent color. Use clean geometry, '
                'simple composition, and editorial balance. Maintain high legibility and product focus. '
                f'{text_block}",\n'
                '  "ratio": "9:16",\n'
                '  "upscale": "Upscale photos to high resolution x2",\n'
                '  "settings": "--no text --no logo --no watermark --no captions --no artifacts --ar 9:16"\n'
                "}"
            ).strip()

        if style == "neobrutalism":
            color = accent_color or "yellow"
            return (
                "{\n"
                '  "model": "nano-banana",\n'
                f'  "prompt": "Create a neo-brutalist illustrated YouTube thumbnail for {product_name}. '
                f'Use bold black outlines, flat solid {color} accents, chunky drop shadows, and playful '
                'geometric shapes. Keep a loud, energetic composition with strong contrast on a clean '
                'background. Maintain crisp edges and premium polish. '
                f'{text_block}",\n'
                '  "ratio": "9:16",\n'
                '  "upscale": "Upscale photos to high resolution x2",\n'
                '  "settings": "--no text --no logo --no watermark --no captions --no artifacts --ar 9:16"\n'
                "}"
            ).strip()

        if style == "vibrant":
            return (
                "{\n"
                '  "model": "nano-banana",\n'
                f'  "prompt": "Create a vibrant, pop-art inspired YouTube thumbnail for {product_name}. '
                'Use saturated colors, dynamic angles, and energetic composition. Strong contrast and '
                'bold shapes should make the product stand out with a premium commercial finish. '
                f'{text_block}",\n'
                '  "ratio": "9:16",\n'
                '  "upscale": "Upscale photos to high resolution x2",\n'
                '  "settings": "--no text --no logo --no watermark --no captions --no artifacts --ar 9:16"\n'
                "}"
            ).strip()

        return (
            "{\n"
            '  "model": "nano-banana",\n'
            f'  "prompt": "Create a dramatic cinematic YouTube thumbnail featuring {product_name}. '
            'Use high-contrast lighting, a focused spotlight on the product, and a moody background. '
            'The composition should feel intense, premium, and high-impact. '
            f'{text_block}",\n'
            '  "ratio": "9:16",\n'
            '  "upscale": "Upscale photos to high resolution x2",\n'
            '  "settings": "--no text --no logo --no watermark --no captions --no artifacts --ar 9:16"\n'
            "}"
        ).strip()

    def generate_ab_test_set(
        self,
        product: dict,
        hook_text: str,
        styles: list[str] = None,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> list[dict]:
        """
        A/B 테스트용 다양한 스타일 썸네일 세트 생성

        Args:
            product: 제품 정보
            hook_text: 공통 훅 텍스트
            styles: 테스트할 스타일 목록 (None이면 전체)

        Returns:
            [{style, image_bytes, description}] 리스트
        """
        if styles is None:
            styles = ["dramatic", "neobrutalism", "vibrant"]

        results = []
        for i, style in enumerate(styles):
            if progress_callback:
                progress_callback(
                    f"스타일 {i + 1}/{len(styles)} 생성 중...",
                    int((i / len(styles)) * 100),
                )

            try:
                image = self.generate(
                    product=product,
                    hook_text=hook_text,
                    style=style,
                )
                results.append(
                    {
                        "style": style,
                        "style_name": THUMBNAIL_STYLES.get(style, {}).get(
                            "name", style
                        ),
                        "image_bytes": image,
                        "description": THUMBNAIL_STYLES.get(style, {}).get(
                            "prompt_modifier", ""
                        ),
                    }
                )
            except Exception as e:
                logger.warning(f"스타일 {style} 생성 실패: {e}")

        return results

    def generate_from_strategy(
        self,
        product: dict,
        strategy: dict,
        count: int = 3,
        styles: Optional[list[str]] = None,
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
            styles=styles,
            progress_callback=progress_callback,
        )

    def get_text_overlay_guide(self) -> dict:
        """텍스트 오버레이 가이드 반환"""
        return TEXT_OVERLAY_GUIDE
