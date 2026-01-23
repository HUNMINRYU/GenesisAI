"""
커스텀 예외 클래스 정의
계층적 예외 구조로 세분화된 에러 핸들링 지원
"""
from typing import Any


class GenesisAIError(Exception):
    """모든 애플리케이션 예외의 기본 클래스"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


# =============================================
# 설정 관련 예외
# =============================================


class ConfigurationError(GenesisAIError):
    """설정 관련 오류"""

    pass


class MissingCredentialsError(ConfigurationError):
    """자격증명 누락 오류"""

    pass


# =============================================
# API 클라이언트 예외
# =============================================


class APIClientError(GenesisAIError):
    """외부 API 클라이언트 오류의 기본 클래스"""

    pass


class YouTubeAPIError(APIClientError):
    """YouTube API 오류"""

    pass


class NaverAPIError(APIClientError):
    """네이버 API 오류"""

    pass


class GeminiAPIError(APIClientError):
    """Gemini AI API 오류"""

    pass


class VeoAPIError(APIClientError):
    """Veo 비디오 생성 오류"""

    pass


# =============================================
# 스토리지 관련 예외
# =============================================


class StorageError(GenesisAIError):
    """스토리지 서비스 오류"""

    pass


class GCSUploadError(StorageError):
    """GCS 업로드 실패"""

    pass


class GCSDownloadError(StorageError):
    """GCS 다운로드 실패"""

    pass


# =============================================
# 검증 관련 예외
# =============================================


class ValidationError(GenesisAIError):
    """데이터 검증 오류"""

    pass


class InvalidProductError(ValidationError):
    """유효하지 않은 제품 오류"""

    pass


class InvalidConfigError(ValidationError):
    """유효하지 않은 설정 오류"""

    pass


# =============================================
# 파이프라인 관련 예외
# =============================================


class PipelineError(GenesisAIError):
    """파이프라인 실행 오류"""

    pass


class DataCollectionError(PipelineError):
    """데이터 수집 단계 오류"""

    pass


class StrategyGenerationError(PipelineError):
    """전략 생성 단계 오류"""

    pass


# =============================================
# 콘텐츠 생성 예외
# =============================================


class ContentGenerationError(GenesisAIError):
    """콘텐츠 생성 실패"""

    pass


class ThumbnailGenerationError(ContentGenerationError):
    """썸네일 생성 실패"""

    pass


class VideoGenerationError(ContentGenerationError):
    """비디오 생성 실패"""

    pass


# =============================================
# 유틸리티 함수
# =============================================


def format_error_for_ui(error: GenesisAIError) -> str:
    """UI 표시용 에러 메시지 포맷팅"""
    error_type = type(error).__name__
    return f"[{error_type}] {error.message}"
