"""
파이프라인 실행 관련 도메인 모델
"""
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class PipelineStep(str, Enum):
    """파이프라인 실행 단계"""

    INITIALIZED = "initialized"
    DATA_COLLECTION = "data_collection"
    YOUTUBE_COLLECTION = "youtube_collection"
    NAVER_COLLECTION = "naver_collection"
    STRATEGY_GENERATION = "strategy_generation"
    THUMBNAIL_CREATION = "thumbnail_creation"
    VIDEO_GENERATION = "video_generation"
    UPLOAD = "upload"
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineConfig(BaseModel):
    """파이프라인 실행 설정"""

    # 데이터 수집 설정
    youtube_count: int = Field(default=3, ge=1, le=10, description="YouTube 검색 결과 수")
    naver_count: int = Field(default=10, ge=5, le=30, description="네이버 쇼핑 검색 결과 수")
    include_comments: bool = Field(default=True, description="댓글 수집 여부")
    include_transcript: bool = Field(default=True, description="자막 수집 여부")

    # 콘텐츠 생성 설정
    generate_thumbnail: bool = Field(default=True, description="썸네일 생성 여부")
    generate_multi_thumbnails: bool = Field(default=False, description="다중 썸네일 생성 여부")
    thumbnail_count: int = Field(default=3, ge=1, le=5, description="생성할 썸네일 수")
    generate_video: bool = Field(default=True, description="비디오 생성 여부")
    video_duration: int = Field(default=8, ge=5, le=30, description="비디오 길이(초)")

    # AI 설정
    use_search_grounding: bool = Field(default=True, description="검색 그라운딩 사용 여부")

    # 저장 설정
    upload_to_gcs: bool = Field(default=True, description="GCS 업로드 여부")


class PipelineProgress(BaseModel):
    """파이프라인 실행 진행 상황"""

    current_step: PipelineStep = Field(default=PipelineStep.INITIALIZED, description="현재 단계")
    step_number: int = Field(default=0, ge=0, description="현재 단계 번호")
    total_steps: int = Field(default=6, ge=1, description="총 단계 수")
    message: str = Field(default="", description="진행 메시지")
    percentage: int = Field(default=0, ge=0, le=100, description="진행률")

    def update(self, step: PipelineStep, message: str = "") -> None:
        """진행 상황 업데이트"""
        self.current_step = step
        self.message = message
        # 단계별 진행률 계산
        step_map = {
            PipelineStep.INITIALIZED: 0,
            PipelineStep.DATA_COLLECTION: 10,
            PipelineStep.YOUTUBE_COLLECTION: 20,
            PipelineStep.NAVER_COLLECTION: 35,
            PipelineStep.STRATEGY_GENERATION: 50,
            PipelineStep.THUMBNAIL_CREATION: 70,
            PipelineStep.VIDEO_GENERATION: 85,
            PipelineStep.UPLOAD: 95,
            PipelineStep.COMPLETED: 100,
            PipelineStep.FAILED: self.percentage,  # 실패 시 현재 진행률 유지
        }
        self.percentage = step_map.get(step, self.percentage)


class CollectedData(BaseModel):
    """수집된 데이터"""

    youtube_data: Optional[dict[str, Any]] = Field(default=None, description="YouTube 데이터")
    naver_data: Optional[dict[str, Any]] = Field(default=None, description="네이버 데이터")
    pain_points: list[dict[str, Any]] = Field(default_factory=list, description="페인 포인트")
    gain_points: list[dict[str, Any]] = Field(default_factory=list, description="게인 포인트")


class GeneratedContent(BaseModel):
    """생성된 콘텐츠"""

    thumbnail_data: Optional[bytes] = Field(default=None, description="썸네일 이미지 바이트")
    thumbnail_url: Optional[str] = Field(default=None, description="썸네일 URL")
    multi_thumbnails: list[dict[str, Any]] = Field(default_factory=list, description="다중 썸네일")
    video_path: Optional[str] = Field(default=None, description="비디오 경로")
    video_url: Optional[str] = Field(default=None, description="비디오 URL")

    class Config:
        arbitrary_types_allowed = True


class PipelineResult(BaseModel):
    """파이프라인 실행 결과"""

    success: bool = Field(..., description="성공 여부")
    product_name: str = Field(..., description="제품명")
    config: Optional[PipelineConfig] = Field(default=None, description="실행 설정")
    collected_data: Optional[CollectedData] = Field(default=None, description="수집된 데이터")
    strategy: Optional[dict[str, Any]] = Field(default=None, description="마케팅 전략")
    generated_content: Optional[GeneratedContent] = Field(default=None, description="생성된 콘텐츠")
    error_message: Optional[str] = Field(default=None, description="에러 메시지")
    executed_at: datetime = Field(default_factory=datetime.now, description="실행 시간")
    duration_seconds: float = Field(default=0.0, ge=0, description="실행 시간(초)")

    class Config:
        arbitrary_types_allowed = True
