"""
도메인 모델 패키지
모든 Pydantic 모델을 중앙 export
"""
from .marketing import (
    CompetitorAnalysis,
    ContentStrategy,
    HookingPoint,
    MarketingStrategy,
    ShortformScenario,
    SNSCopy,
    TargetPersona,
)
from .naver import (
    CompetitorStats,
    NaverProduct,
    NaverSearchResult,
)
from .pipeline import (
    CollectedData,
    GeneratedContent,
    PipelineConfig,
    PipelineProgress,
    PipelineResult,
    PipelineStep,
)
from .product import (
    Product,
    ProductCatalog,
    ProductCategory,
)
from .youtube import (
    GainPoint,
    PainPoint,
    YouTubeComment,
    YouTubeSearchResult,
    YouTubeVideo,
)

__all__ = [
    # Product
    "Product",
    "ProductCatalog",
    "ProductCategory",
    # YouTube
    "YouTubeVideo",
    "YouTubeComment",
    "YouTubeSearchResult",
    "PainPoint",
    "GainPoint",
    # Naver
    "NaverProduct",
    "NaverSearchResult",
    "CompetitorStats",
    # Marketing
    "TargetPersona",
    "HookingPoint",
    "ShortformScenario",
    "SNSCopy",
    "CompetitorAnalysis",
    "ContentStrategy",
    "MarketingStrategy",
    # Pipeline
    "PipelineStep",
    "PipelineConfig",
    "PipelineProgress",
    "PipelineResult",
    "CollectedData",
    "GeneratedContent",
]
