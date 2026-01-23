"""
세션 상태 관리
Streamlit session_state 중앙화 관리
"""
from typing import Any, Optional

import streamlit as st

from ...core.models import PipelineConfig, PipelineProgress, PipelineStep


class SessionManager:
    """세션 상태 관리자"""

    # 세션 키 상수
    SELECTED_PRODUCT = "selected_product"
    COLLECTED_DATA = "collected_data"
    PIPELINE_STRATEGY = "pipeline_strategy"
    PIPELINE_PROGRESS = "pipeline_progress"
    PIPELINE_CONFIG = "pipeline_config"
    GENERATED_THUMBNAIL = "generated_thumbnail"
    GENERATED_VIDEO = "generated_video"
    YOUTUBE_DATA = "youtube_data"
    NAVER_DATA = "naver_data"

    @classmethod
    def init_session_state(cls) -> None:
        """세션 상태 초기화"""
        defaults = {
            cls.SELECTED_PRODUCT: None,
            cls.COLLECTED_DATA: None,
            cls.PIPELINE_STRATEGY: None,
            cls.PIPELINE_PROGRESS: PipelineProgress(),
            cls.PIPELINE_CONFIG: PipelineConfig(),
            cls.GENERATED_THUMBNAIL: None,
            cls.GENERATED_VIDEO: None,
            cls.YOUTUBE_DATA: None,
            cls.NAVER_DATA: None,
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """세션 값 조회"""
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """세션 값 설정"""
        st.session_state[key] = value

    @classmethod
    def reset(cls) -> None:
        """세션 상태 초기화"""
        keys_to_reset = [
            cls.COLLECTED_DATA,
            cls.PIPELINE_STRATEGY,
            cls.GENERATED_THUMBNAIL,
            cls.GENERATED_VIDEO,
            cls.YOUTUBE_DATA,
            cls.NAVER_DATA,
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = None

        st.session_state[cls.PIPELINE_PROGRESS] = PipelineProgress()

    # 편의 메서드들
    @classmethod
    def get_selected_product(cls) -> Optional[dict]:
        """선택된 제품 반환"""
        return cls.get(cls.SELECTED_PRODUCT)

    @classmethod
    def set_selected_product(cls, product: dict) -> None:
        """선택된 제품 설정"""
        cls.set(cls.SELECTED_PRODUCT, product)

    @classmethod
    def get_collected_data(cls) -> Optional[dict]:
        """수집된 데이터 반환"""
        return cls.get(cls.COLLECTED_DATA)

    @classmethod
    def set_collected_data(cls, data: dict) -> None:
        """수집된 데이터 설정"""
        cls.set(cls.COLLECTED_DATA, data)

    @classmethod
    def get_pipeline_progress(cls) -> PipelineProgress:
        """파이프라인 진행 상황 반환"""
        return cls.get(cls.PIPELINE_PROGRESS, PipelineProgress())

    @classmethod
    def update_pipeline_progress(cls, step: PipelineStep, message: str = "") -> None:
        """파이프라인 진행 상황 업데이트"""
        progress = cls.get_pipeline_progress()
        progress.update(step, message)
        cls.set(cls.PIPELINE_PROGRESS, progress)

    @classmethod
    def get_pipeline_config(cls) -> PipelineConfig:
        """파이프라인 설정 반환"""
        return cls.get(cls.PIPELINE_CONFIG, PipelineConfig())

    @classmethod
    def set_pipeline_config(cls, config: PipelineConfig) -> None:
        """파이프라인 설정 저장"""
        cls.set(cls.PIPELINE_CONFIG, config)

    @classmethod
    def has_collected_data(cls) -> bool:
        """데이터 수집 여부 확인"""
        return cls.get(cls.COLLECTED_DATA) is not None

    @classmethod
    def has_strategy(cls) -> bool:
        """전략 생성 여부 확인"""
        return cls.get(cls.PIPELINE_STRATEGY) is not None
