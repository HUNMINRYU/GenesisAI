import asyncio
import json
from typing import List

from genesis_ai.core.interfaces.ai_service import IMarketingAIService
from genesis_ai.services.pipeline.types import Candidate, CandidateFeatures


class FeatureHydrator:
    """
    X-Algorithm의 Hydration 단계 (LLM Feature Extraction)
    단순 댓글 텍스트 -> Rich Feature (구매의도, 바이럴 가능성 등) 변환
    """

    def __init__(self, gemini_client: IMarketingAIService):
        self.gemini_client = gemini_client

    async def hydrate(self, candidates: List[Candidate]) -> List[Candidate]:
        """
        Gemini를 통해 댓글들의 Feature를 추출하고 채워넣음
        (비용 효율성을 위해 배치 처리 권장, 여기선 단순 Loop/Async 예시)
        """
        if not candidates:
            return []

        # 프롬프트 구성 (한 번에 여러 개 분석 가능하지만, 정밀도를 위해 개별 or 소량 배치)
        # 여기선 간단히 1:1로 구현하되, 추후 Batch 로직으로 고도화 가능
        tasks = [self._analyze_single_comment(c) for c in candidates]
        results = await asyncio.gather(*tasks)

        return results

    async def _analyze_single_comment(self, candidate: Candidate) -> Candidate:
        # Prompt Engineering for Feature Extraction
        prompt = f"""
        Analyze the following user comment and extract engagement features.
        Return ONLY a JSON object with values between 0.0 and 1.0.

        Comment: "{candidate.content}"

        JSON Schema:
        {{
            "purchase_intent": float,      # Is the user interested in buying?
            "reply_inducing": float,       # Does this provoke a reply or discussion?
            "constructive_feedback": float,# Is this detailed, specific feedback?
            "sentiment_intensity": float,  # How strong is the emotion?
            "toxicity": float,             # Is this spam/hate speech?
            "keywords": [str]              # Top 2-3 keywords
        }}
        """

        try:
            # Gemini 호출 (시스템 인스트럭션 등은 Client 내부 설정 활용)
            response_text = await self.gemini_client.generate_content_async(prompt)

            # JSON 파싱 (마크다운 코드블록 제거 처리)
            cleaned_text = (
                response_text.replace("```json", "").replace("```", "").strip()
            )
            data = json.loads(cleaned_text)

            # Feature 객체 생성 및 주입
            features = CandidateFeatures(
                purchase_intent=data.get("purchase_intent", 0.0),
                reply_inducing=data.get("reply_inducing", 0.0),
                constructive_feedback=data.get("constructive_feedback", 0.0),
                sentiment_intensity=data.get("sentiment_intensity", 0.0),
                toxicity=data.get("toxicity", 0.0),
                keywords=data.get("keywords", []),
            )
            candidate.features = features

        except Exception as e:
            # 실패 시 기본값 (0.0) 유지, 로깅 필요
            print(f"Hydration failed for comment {candidate.id}: {e}")

        return candidate
