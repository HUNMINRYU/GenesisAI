"""
후킹 서비스
AI 기반 마케팅 후킹 문구 자동 생성
"""

from ..utils.logger import get_logger, log_step, log_success

logger = get_logger(__name__)


# === 후킹 스타일 템플릿 ===
HOOK_STYLES = {
    "curiosity": {
        "name": "호기심형",
        "emoji": "🤔",
        "templates": [
            "99%가 모르는 {product}의 비밀",
            "{product} 이렇게 쓰면 효과 2배",
            "전문가들만 아는 {product} 활용법",
            "{benefit} 하려면 이것만 기억하세요",
        ],
        "description": "시청자의 호기심을 자극하여 끝까지 시청하게 만듦",
    },
    "fear": {
        "name": "공포형",
        "emoji": "😱",
        "templates": [
            "이거 안 쓰면 {pain_point} 계속됩니다",
            "{pain_point} 방치하면 이렇게 됩니다",
            "아직도 {wrong_method} 하세요? 큰일납니다",
            "{product} 없이 버티다간...",
        ],
        "description": "문제를 방치했을 때의 결과를 보여줌",
    },
    "reversal": {
        "name": "반전형",
        "emoji": "😮",
        "templates": [
            "처음엔 의심했는데... {benefit}",
            "솔직히 안 믿었어요, 근데 {result}",
            "이게 된다고? {product} 써보니까...",
            "거짓말인 줄 알았는데 {benefit} 실화",
        ],
        "description": "의심에서 확신으로의 전환 스토리",
    },
    "question": {
        "name": "질문형",
        "emoji": "❓",
        "templates": [
            "{pain_point} 고민이시죠?",
            "혹시 {pain_point} 때문에 고민 중이세요?",
            "{wrong_method} 하고 계신가요?",
            "{benefit} 원하시나요?",
        ],
        "description": "시청자의 고민에 공감하며 시작",
    },
    "urgency": {
        "name": "긴급형",
        "emoji": "⚡",
        "templates": [
            "지금 안 보면 후회합니다",
            "오늘만 공개되는 {product} 비법",
            "이 영상 내리기 전에 꼭 보세요",
            "{benefit} 원하면 지금 당장!",
        ],
        "description": "긴급함을 강조하여 즉시 행동 유도",
    },
    # === 심리 모델 (Marketing Psychology) ===
    "loss_aversion": {
        "name": "손실 회피형",
        "emoji": "📉",
        "templates": [
            "이 기회 놓치면 {loss} 손해봅니다",
            "오늘 지나면 혜택이 사라져요",
            "남들 다 {benefit} 받는데 혼자만...",
            "지금 안 쓰면 나중에 후회합니다",
        ],
        "description": "얻는 기쁨보다 잃는 고통이 2배 더 크다는 심리 활용",
    },
    "social_proof": {
        "name": "사회적 증거형",
        "emoji": "👥",
        "templates": [
            "이미 10만 명이 선택한 {product}",
            "왜 다들 {product} 이야기만 할까요?",
            "인기 폭발! {product} 써본 사람들 반응",
            "요즘 핫한 {product}, 이유가 있네요",
        ],
        "description": "남들도 다 쓴다! 대세감을 조성하여 안심시킴",
    },
    "authority": {
        "name": "권위 활용형",
        "emoji": "👨‍⚕️",
        "templates": [
            "전문가가 추천하는 {product} 사용법",
            "업계 1위가 {product} 선택한 이유",
            "의사/전문가들도 인정한 {benefit} 비결",
            "연구 결과로 증명된 {product} 효과",
        ],
        "description": "권위자의 추천이나 데이터를 통해 신뢰도 확보",
    },
    "scarcity": {
        "name": "희소성 강조형",
        "emoji": "⏳",
        "templates": [
            "딱 100개만 남았습니다",
            "지금 아니면 구할 수 없는 {product}",
            "재입고 문의 폭주! 품절 임박",
            "이번 달만 가능한 {benefit} 혜택",
        ],
        "description": "부족함을 강조하여 소유욕과 긴박감 자극",
    },
    "zeigarnik": {
        "name": "미완성 효과형",
        "emoji": "🧩",
        "templates": [
            "{product}의 숨겨진 기능 하나만 알면...",
            "이것만 알았어도 {pain_point} 없었을 텐데",
            "딱 하나만 바꿨는데 {benefit} 대박남",
            "99%가 놓치고 있는 {product} 사용 꿀팁",
        ],
        "description": "문장을 미완성처럼 느끼게 하여 궁금증 극대화",
    },
}


class HookService:
    """AI 기반 후킹 문구 생성 서비스"""

    def __init__(self, gemini_client=None) -> None:
        """
        Args:
            gemini_client: AI 기반 맞춤 후킹 생성 시 사용 (선택)
        """
        self._gemini = gemini_client

    def get_available_styles(self) -> list[dict]:
        """사용 가능한 후킹 스타일 목록 반환"""
        return [
            {
                "key": key,
                "name": style["name"],
                "emoji": style["emoji"],
                "description": style["description"],
            }
            for key, style in HOOK_STYLES.items()
        ]

    def generate_hooks(
        self,
        style: str,
        product: dict,
        pain_points: list[str] = None,
        count: int = 3,
    ) -> list[str]:
        """
        특정 스타일의 후킹 문구 생성

        Args:
            style: 후킹 스타일 키 (curiosity, fear, reversal 등)
            product: 제품 정보 딕셔너리
            pain_points: 고객 페인포인트 목록
            count: 생성할 후킹 문구 수

        Returns:
            후킹 문구 리스트
        """
        log_step("후킹 생성", style, f"제품: {product.get('name', 'N/A')}")

        if style not in HOOK_STYLES:
            style = "curiosity"  # 기본값

        style_data = HOOK_STYLES[style]
        templates = style_data["templates"]

        # 템플릿 변수 준비
        p_name = product.get("name", "제품")
        p_benefit = product.get("benefit", "효과를 경험")

        pain_point = "고민"
        if pain_points and len(pain_points) > 0:
            pain_point = pain_points[0]
        elif product.get("pain_points"):
            pain_point = product["pain_points"][0]

        # 템플릿 채우기
        hooks = []
        for i, template in enumerate(templates[:count]):
            hook = template.format(
                product=p_name,
                benefit=p_benefit,
                pain_point=pain_point,
                wrong_method="기존 방법",
                result="진짜 효과가 있더라",
            )
            # 이모지 추가
            hooks.append(f"{style_data['emoji']} {hook}")

        log_success(f"{len(hooks)}개 후킹 문구 생성 완료")
        return hooks

    # === Marketing Psychology Methods (Skill 적용) ===

    def generate_loss_aversion_hooks(self, product: dict, count: int = 3) -> list[str]:
        """손실 회피(Loss Aversion) 모델 적용 훅 생성"""
        return self.generate_hooks("loss_aversion", product, count=count)

    def generate_social_proof_hooks(self, product: dict, count: int = 3) -> list[str]:
        """사회적 증거(Social Proof) 모델 적용 훅 생성"""
        return self.generate_hooks("social_proof", product, count=count)

    def generate_authority_hooks(self, product: dict, count: int = 3) -> list[str]:
        """권위(Authority) 모델 적용 훅 생성"""
        return self.generate_hooks("authority", product, count=count)

    def generate_scarcity_hooks(self, product: dict, count: int = 3) -> list[str]:
        """희소성(Scarcity) 모델 적용 훅 생성"""
        return self.generate_hooks("scarcity", product, count=count)

    def generate_zeigarnik_hooks(self, product: dict, count: int = 3) -> list[str]:
        """자이가르닉(Zeigarnik) 효과 모델 적용 훅 생성"""
        return self.generate_hooks("zeigarnik", product, count=count)

    def generate_multi_style_hooks(
        self,
        product: dict,
        pain_points: list[str] = None,
        styles: list[str] = None,
    ) -> dict[str, list[str]]:
        """
        여러 스타일의 후킹 문구 일괄 생성

        Args:
            product: 제품 정보
            pain_points: 페인포인트 목록
            styles: 생성할 스타일 목록 (None이면 전체)

        Returns:
            {스타일: [후킹문구들]} 딕셔너리
        """
        if styles is None:
            styles = list(HOOK_STYLES.keys())

        results = {}
        for style in styles:
            results[style] = self.generate_hooks(
                style=style,
                product=product,
                pain_points=pain_points,
                count=2,  # 각 스타일당 2개
            )

        return results

    async def generate_ai_hooks(
        self,
        product: dict,
        pain_points: list[str],
        target_audience: dict,
        count: int = 5,
    ) -> list[str]:
        """
        AI(Gemini)를 활용한 맞춤 후킹 문구 생성

        Args:
            product: 제품 정보
            pain_points: 고객 페인포인트
            target_audience: 타겟 오디언스 정보
            count: 생성할 후킹 수

        Returns:
            AI가 생성한 후킹 문구 리스트
        """
        if not self._gemini:
            # AI 클라이언트 없으면 템플릿 기반으로 폴백
            return self.generate_hooks("curiosity", product, pain_points, count)

        prompt = f"""
당신은 숏폼 영상 마케팅 전문가입니다.
다음 제품에 대해 시청자의 시선을 사로잡는 후킹 문구 {count}개를 생성하세요.

## 제품 정보
- 제품명: {product.get("name", "N/A")}
- 카테고리: {product.get("category", "N/A")}
- 핵심 효과: {product.get("benefit", "N/A")}

## 타겟 오디언스
- 주요 타겟: {target_audience.get("primary", "일반 소비자")}
- 페인포인트: {", ".join(pain_points[:3]) if pain_points else "없음"}

## 요구사항
1. 첫 3초 안에 시청자를 사로잡아야 함
2. 15자 이내로 간결하게
3. 감정을 자극하는 단어 사용
4. 다양한 스타일 (호기심, 공포, 질문, 반전 등) 혼합

## 출력 형식
각 줄에 하나의 후킹 문구만 출력 (이모지 포함)
"""

        try:
            response = await self._gemini.generate_text_async(prompt)
            hooks = [line.strip() for line in response.split("\n") if line.strip()]
            return hooks[:count]
        except Exception as e:
            logger.warning(f"AI 후킹 생성 실패, 템플릿 사용: {e}")
            return self.generate_hooks("curiosity", product, pain_points, count)

    def get_best_hooks_for_video(
        self,
        product: dict,
        video_style: str = "dramatic",
        pain_points: list[str] = None,
    ) -> list[dict]:
        """
        비디오 스타일에 맞는 최적의 후킹 조합 반환

        Args:
            product: 제품 정보
            video_style: 비디오 스타일 (dramatic, calm, horror 등)
            pain_points: 페인포인트

        Returns:
            [{style, hook, recommended_for}] 리스트
        """
        # 비디오 스타일별 추천 후킹 스타일
        style_mapping = {
            "dramatic": ["urgency", "reversal", "fear"],
            "calm": ["question", "curiosity", "social_proof"],
            "horror": ["fear", "urgency", "question"],
            "commercial": ["curiosity", "social_proof", "reversal"],
        }

        recommended_styles = style_mapping.get(
            video_style, ["curiosity", "fear", "question"]
        )

        results = []
        for style in recommended_styles:
            hooks = self.generate_hooks(style, product, pain_points, count=1)
            if hooks:
                results.append(
                    {
                        "style": style,
                        "style_name": HOOK_STYLES[style]["name"],
                        "hook": hooks[0],
                        "recommended_for": video_style,
                    }
                )

        return results
