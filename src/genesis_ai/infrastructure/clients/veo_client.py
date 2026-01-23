"""
Veo 비디오 생성 클라이언트
Vertex AI Veo 3.1 기반 마케팅 비디오 생성
"""
import time
from datetime import datetime
from typing import Callable, Optional

from ...config.constants import CAMERA_MOTIONS
from ...core.exceptions import VeoAPIError
from ...utils.logger import get_logger

logger = get_logger(__name__)


class VeoClient:
    """Veo 비디오 생성 클라이언트"""

    def __init__(
        self,
        project_id: str,
        location: str,
        gcs_bucket_name: str,
        model_id: str = "veo-3.1-fast-generate-001",
    ) -> None:
        self._project_id = project_id
        self._location = location
        self._gcs_bucket_name = gcs_bucket_name
        self._model_id = model_id
        self._client = None

    def _get_client(self):
        """Genai 클라이언트 인스턴스 반환 (지연 초기화)"""
        if self._client is None:
            from google import genai

            self._client = genai.Client()
        return self._client

    def is_configured(self) -> bool:
        """설정 확인"""
        return bool(self._project_id and self._gcs_bucket_name)

    def health_check(self) -> bool:
        """API 연결 상태 확인"""
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def get_available_motions(self) -> list[str]:
        """사용 가능한 카메라 모션 목록"""
        return CAMERA_MOTIONS.copy()

    def generate_marketing_prompt(
        self,
        product: dict,
        insights: dict,
        hook_text: str = "",
    ) -> str:
        """마케팅용 비디오 프롬프트 생성"""
        hook = hook_text or insights.get("hook", "벌레 싹!")
        style = insights.get("style", "cinematic")
        mood = insights.get("mood", "dramatic")

        style_desc = {
            "cinematic": "cinematic film-like quality with shallow depth of field",
            "commercial": "polished commercial advertisement broadcast quality",
            "horror": "dark suspenseful horror movie aesthetic with tension",
            "documentary": "documentary-style realistic natural footage",
        }.get(style, "cinematic professional quality")

        mood_desc = {
            "dramatic": "dramatic intense high-stakes atmosphere",
            "urgent": "urgent fast-paced action with quick movements",
            "hopeful": "hopeful optimistic uplifting bright feeling",
            "calm": "calm serene peaceful soothing environment",
        }.get(mood, "dramatic impactful atmosphere")

        product_name = product.get("name", "")
        product_target = product.get("target", "해충")

        return f"""
SUBJECT: Professional pest control product "{product_name}" with blue packaging and modern design.
A professional pest control solution designed for {product_target}.

SETTING: Modern Korean home with clean kitchen environment, bright natural lighting.
The scene transitions from a problem state (pest infestation) to a solution state (pest-free clean environment).

ACTION: Dynamic product demonstration sequence:
- Initial: Reveal of pest problem (subtle, not graphic)
- Middle: Product application with satisfying spray effect
- Climax: Pests flee or disappear with visual effect
- Final: Clean, protected home environment with satisfied homeowner

STYLE: {style_desc}. {mood_desc}.
Premium Korean vertical advertisement (9:16), vibrant colors, professional marketing aesthetic.

CAMERA MOVEMENT:
- Opening: Wide establishing shot of the scene
- Middle: Smooth dolly movement, close-up product shots
- Close: Low-angle hero shot of the protected space
- Final: Wide clean home reveal

COMPOSITION:
- Product centered with blue glow effect
- Text overlay "{hook}" in bold Korean typography
- Before/after visual contrast
- Vertical 9:16 format for mobile shortform

LIGHTING AND MOOD:
- Cool blue tones transitioning to warm golden light
- Bright key light with soft fill
- Emphasizing product cleanliness and home freshness
- Subtle lens flare during transformation moment

AUDIO ELEMENTS:
- Background: Low suspenseful hum builds tension initially
- SFX: Satisfying spray sound effect during product action
- Transition: Crisp clean "whoosh" sound as scene transforms
- Music: Upbeat Korean advertisement music
- End: Brief triumphant musical sting with confident voiceover tone

NEGATIVE PROMPT: watermarks, text overlays with errors, subtitles, blurry, low quality, unprofessional appearance.
""".strip()

    def generate_video(
        self,
        prompt: str,
        duration_seconds: int = 8,
        resolution: str = "720p",
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | str:
        """텍스트 프롬프트로 비디오 생성"""
        logger.info(f"비디오 생성 시작: {duration_seconds}초, {resolution}")

        try:
            from google.genai.types import GenerateVideosConfig

            client = self._get_client()

            date_str = datetime.now().strftime("%Y%m%d")
            output_gcs_uri = f"gs://{self._gcs_bucket_name}/videos/{date_str}/"

            if progress_callback:
                progress_callback(f"Veo API 요청 전송 중... ({duration_seconds}초, {resolution})", 10)

            operation = client.models.generate_videos(
                model=self._model_id,
                prompt=prompt,
                config=GenerateVideosConfig(
                    aspect_ratio="9:16",
                    output_gcs_uri=output_gcs_uri,
                    duration_seconds=duration_seconds,
                    generate_audio=True,
                    number_of_videos=1,
                    resolution=resolution,
                    negative_prompt="watermarks, text overlays, subtitles, blurry, low quality",
                    person_generation="allow_adult",
                ),
            )

            if progress_callback:
                progress_callback("작업 시작됨", 20)

            # 비동기 폴링
            max_wait = 180 if duration_seconds > 8 else 120
            waited = 0

            while not operation.done and waited < max_wait:
                time.sleep(10)
                waited += 10
                operation = client.operations.get(operation)

                if progress_callback:
                    progress = min(20 + int((waited / max_wait) * 60), 80)
                    progress_callback(f"생성 중... ({waited}초)", progress)

            if operation.done and operation.result:
                video = operation.result.generated_videos[0]
                video_uri = video.video.uri

                logger.info(f"비디오 생성 완료: {video_uri}")

                if progress_callback:
                    progress_callback("비디오 다운로드 중...", 85)

                # GCS에서 다운로드
                try:
                    from google.cloud import storage as gcs_storage

                    gcs_client = gcs_storage.Client()
                    path_parts = video_uri.replace("gs://", "").split("/", 1)
                    bucket_name = path_parts[0]
                    blob_path = path_parts[1] if len(path_parts) > 1 else ""

                    bucket = gcs_client.bucket(bucket_name)
                    blob = bucket.blob(blob_path)
                    video_content = blob.download_as_bytes()

                    if progress_callback:
                        progress_callback("비디오 생성 완료!", 100)

                    return video_content

                except Exception as download_error:
                    logger.error(f"비디오 다운로드 오류: {download_error}")
                    return f"영상 생성됨 (GCS): {video_uri}\n다운로드 오류: {download_error}"

            return f"영상 생성 진행 중 (백그라운드)\nGCS에서 확인: {output_gcs_uri}"

        except Exception as e:
            logger.error(f"비디오 생성 실패: {e}")
            raise VeoAPIError(f"비디오 생성 실패: {e}")

    def generate_video_from_image(
        self,
        image_bytes: bytes,
        prompt: str,
        duration_seconds: int = 8,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> bytes | None:
        """이미지 기반 비디오 생성"""
        # TODO: 이미지 기반 비디오 생성 구현
        logger.warning("이미지 기반 비디오 생성은 아직 구현되지 않았습니다.")
        return None

    def generate_multi_video_prompts(
        self,
        product: dict,
        base_hook: str,
        duration_seconds: int = 8,
    ) -> list[dict]:
        """3가지 스타일의 비디오 프롬프트 생성"""
        styles = [
            {"type": "공포형", "style": "horror", "mood": "urgent", "hook": f"😱 {base_hook}"},
            {"type": "정보형", "style": "commercial", "mood": "hopeful", "hook": f"💡 {base_hook}"},
            {"type": "유머형", "style": "commercial", "mood": "hopeful", "hook": f"😂 {base_hook}"},
        ]

        results = []
        for s in styles:
            insights = {"hook": s["hook"], "style": s["style"], "mood": s["mood"]}
            prompt = self.generate_marketing_prompt(product, insights)

            results.append({
                "type": s["type"],
                "hook": s["hook"],
                "prompt": prompt,
                "duration": duration_seconds,
            })

            logger.info(f"{s['type']} 영상 프롬프트 생성 완료")

        return results
