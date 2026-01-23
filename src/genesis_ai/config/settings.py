"""
환경변수 기반 설정 관리
Pydantic Settings를 사용하여 안전하게 API 키 및 설정 관리

Note: YouTube/Gemini는 Vertex AI를 사용하므로 GCP 서비스 계정으로 통합 인증
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class GCPSettings(BaseSettings):
    """GCP 설정 (Vertex AI 통합 인증)"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    project_id: str = Field(..., validation_alias="GOOGLE_CLOUD_PROJECT_ID")
    location: str = Field(
        default="us-central1", validation_alias="GOOGLE_CLOUD_LOCATION"
    )
    gcs_bucket_name: str = Field(..., validation_alias="GCS_BUCKET_NAME")
    credentials_path: Optional[str] = Field(
        default=None, validation_alias="GOOGLE_APPLICATION_CREDENTIALS"
    )

    # Vertex AI 통합 API 키 (YouTube, Gemini 공용)
    google_api_key: SecretStr = Field(..., validation_alias="GOOGLE_API_KEY")


class NaverSettings(BaseSettings):
    """네이버 API 설정"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    client_id: SecretStr = Field(..., validation_alias="NAVER_CLIENT_ID")
    client_secret: SecretStr = Field(..., validation_alias="NAVER_CLIENT_SECRET")


class AIModelSettings(BaseSettings):
    """AI 모델 설정"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    gemini_text_model: str = Field(
        default="gemini-3-pro-preview", validation_alias="GEMINI_TEXT_MODEL"
    )
    gemini_image_model: str = Field(
        default="gemini-3-pro-image-preview", validation_alias="GEMINI_IMAGE_MODEL"
    )
    veo_model_id: str = Field(
        default="veo-3.1-fast-generate-001", validation_alias="VEO_MODEL_ID"
    )


class AppSettings(BaseSettings):
    """애플리케이션 전체 설정"""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "Genesis AI Studio"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")


class Settings:
    """통합 설정 클래스"""

    def __init__(self) -> None:
        self.app = AppSettings()
        self.gcp = GCPSettings()
        self.naver = NaverSettings()
        self.models = AIModelSettings()

    @property
    def google_api_key(self) -> str:
        """Google API 키 반환 (YouTube, Gemini 공용)"""
        return self.gcp.google_api_key.get_secret_value()

    def setup_environment(self) -> None:
        """GCP 환경변수 설정 (Vertex AI용)"""
        import os

        os.environ["GOOGLE_CLOUD_PROJECT"] = self.gcp.project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = self.gcp.location
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"

        if self.gcp.credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self.gcp.credentials_path


@lru_cache()
def get_settings() -> Settings:
    """캐시된 설정 인스턴스 반환"""
    return Settings()
