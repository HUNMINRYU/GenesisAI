"""
Pydantic 모델 단위 테스트
"""
import pytest
from pydantic import ValidationError

from src.genesis_ai.core.models import (
    Product,
    ProductCategory,
    PipelineConfig,
    PipelineProgress,
    PipelineStep,
    HookingPoint,
    MarketingStrategy,
)


class TestProduct:
    """Product 모델 테스트"""

    def test_create_valid_product(self):
        """유효한 제품 생성"""
        product = Product(
            name="테스트 제품",
            category=ProductCategory.PEST_CONTROL,
            description="테스트 설명",
            target="해충",
        )
        assert product.name == "테스트 제품"
        assert product.category == ProductCategory.PEST_CONTROL

    def test_product_to_dict(self):
        """제품 딕셔너리 변환"""
        product = Product(
            name="벅스델타",
            category=ProductCategory.PEST_CONTROL,
            description="델타메트린 기반",
            target="모든 해충",
        )
        d = product.to_dict()
        assert d["name"] == "벅스델타"
        assert d["category"] == "해충방제"

    def test_product_immutable(self):
        """제품 불변성 확인"""
        product = Product(
            name="테스트",
            category=ProductCategory.TRAP,
            description="설명",
            target="대상",
        )
        with pytest.raises(ValidationError):
            product.name = "변경"  # frozen=True


class TestPipelineConfig:
    """PipelineConfig 모델 테스트"""

    def test_default_values(self):
        """기본값 확인"""
        config = PipelineConfig()
        assert config.youtube_count == 3
        assert config.naver_count == 10
        assert config.generate_thumbnail is True
        assert config.generate_video is True

    def test_custom_values(self):
        """커스텀 값 설정"""
        config = PipelineConfig(
            youtube_count=5,
            naver_count=20,
            generate_video=False,
        )
        assert config.youtube_count == 5
        assert config.naver_count == 20
        assert config.generate_video is False

    def test_validation_constraints(self):
        """유효성 검증"""
        with pytest.raises(ValidationError):
            PipelineConfig(youtube_count=0)  # ge=1

        with pytest.raises(ValidationError):
            PipelineConfig(youtube_count=100)  # le=10


class TestPipelineProgress:
    """PipelineProgress 모델 테스트"""

    def test_initial_state(self):
        """초기 상태 확인"""
        progress = PipelineProgress()
        assert progress.current_step == PipelineStep.INITIALIZED
        assert progress.percentage == 0

    def test_update_progress(self):
        """진행 상황 업데이트"""
        progress = PipelineProgress()
        progress.update(PipelineStep.DATA_COLLECTION, "데이터 수집 중")
        assert progress.current_step == PipelineStep.DATA_COLLECTION
        assert progress.message == "데이터 수집 중"
        assert progress.percentage == 10

    def test_completion_progress(self):
        """완료 진행률"""
        progress = PipelineProgress()
        progress.update(PipelineStep.COMPLETED, "완료")
        assert progress.percentage == 100


class TestHookingPoint:
    """HookingPoint 모델 테스트"""

    def test_create_hook(self):
        """훅 포인트 생성"""
        hook = HookingPoint(
            hook="지금 안 사면 후회!",
            hook_type="loss_aversion",
            viral_score=85,
        )
        assert hook.hook == "지금 안 사면 후회!"
        assert hook.hook_type == "loss_aversion"
        assert hook.viral_score == 85

    def test_viral_score_bounds(self):
        """바이럴 점수 범위 검증"""
        with pytest.raises(ValidationError):
            HookingPoint(hook="테스트", hook_type="test", viral_score=101)

        with pytest.raises(ValidationError):
            HookingPoint(hook="테스트", hook_type="test", viral_score=-1)
