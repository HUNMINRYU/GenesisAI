# -*- coding: utf-8 -*-
"""
Streamlit 세션 상태 관리자.
"""
from typing import Any, Optional

import streamlit as st

from ...core.models import PipelineConfig, PipelineProgress, PipelineStep


class SessionManager:
    """세션 상태 관리자."""

    SELECTED_PRODUCT = "selected_product"
    COLLECTED_DATA = "collected_data"
    PIPELINE_STRATEGY = "pipeline_strategy"
    PIPELINE_RESULT = "pipeline_result"
    PIPELINE_PROGRESS = "pipeline_progress"
    PIPELINE_CONFIG = "pipeline_config"
    GENERATED_THUMBNAIL = "generated_thumbnail"
    GENERATED_VIDEO = "generated_video"
    GENERATED_THUMBNAIL_URL = "generated_thumbnail_url"
    GENERATED_VIDEO_URL = "generated_video_url"
    GENERATED_THUMBNAIL_PATH = "generated_thumbnail_path"
    GENERATED_VIDEO_PATH = "generated_video_path"
    GENERATED_METADATA_PATH = "generated_metadata_path"
    YOUTUBE_DATA = "youtube_data"
    NAVER_DATA = "naver_data"
    MULTI_THUMBNAILS = "multi_thumbnails"
    PIPELINE_EXECUTED = "pipeline_executed"
    VIDEO_BYTES = "video_bytes"

    @classmethod
    def init_session_state(cls) -> None:
        """세션 상태 기본값 초기화."""
        defaults = {
            cls.SELECTED_PRODUCT: None,
            cls.COLLECTED_DATA: None,
            cls.PIPELINE_STRATEGY: None,
            cls.PIPELINE_RESULT: None,
            cls.PIPELINE_PROGRESS: PipelineProgress(),
            cls.PIPELINE_CONFIG: PipelineConfig(),
            cls.GENERATED_THUMBNAIL: None,
            cls.GENERATED_VIDEO: None,
            cls.GENERATED_THUMBNAIL_URL: None,
            cls.GENERATED_VIDEO_URL: None,
            cls.GENERATED_THUMBNAIL_PATH: None,
            cls.GENERATED_VIDEO_PATH: None,
            cls.GENERATED_METADATA_PATH: None,
            cls.YOUTUBE_DATA: None,
            cls.NAVER_DATA: None,
            cls.MULTI_THUMBNAILS: None,
            cls.PIPELINE_EXECUTED: False,
            cls.VIDEO_BYTES: None,
        }

        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value

    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """세션 값 조회."""
        return st.session_state.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """세션 값 설정."""
        st.session_state[key] = value

    @classmethod
    def reset(cls) -> None:
        """세션 상태 초기화."""
        keys_to_reset = [
            cls.COLLECTED_DATA,
            cls.PIPELINE_STRATEGY,
            cls.PIPELINE_RESULT,
            cls.GENERATED_THUMBNAIL,
            cls.GENERATED_VIDEO,
            cls.GENERATED_THUMBNAIL_URL,
            cls.GENERATED_VIDEO_URL,
            cls.GENERATED_THUMBNAIL_PATH,
            cls.GENERATED_VIDEO_PATH,
            cls.GENERATED_METADATA_PATH,
            cls.YOUTUBE_DATA,
            cls.NAVER_DATA,
            cls.MULTI_THUMBNAILS,
            cls.VIDEO_BYTES,
        ]
        for key in keys_to_reset:
            if key in st.session_state:
                st.session_state[key] = None

        st.session_state[cls.PIPELINE_PROGRESS] = PipelineProgress()
        st.session_state[cls.PIPELINE_CONFIG] = PipelineConfig()
        st.session_state[cls.PIPELINE_EXECUTED] = False

    @classmethod
    def reset_pipeline_state(cls) -> None:
        """파이프라인 실행 관련 상태만 초기화."""
        for key in (
            cls.COLLECTED_DATA,
            cls.PIPELINE_STRATEGY,
            cls.PIPELINE_RESULT,
            cls.GENERATED_THUMBNAIL,
            cls.GENERATED_VIDEO,
            cls.GENERATED_THUMBNAIL_URL,
            cls.GENERATED_VIDEO_URL,
            cls.GENERATED_THUMBNAIL_PATH,
            cls.GENERATED_VIDEO_PATH,
            cls.GENERATED_METADATA_PATH,
            cls.MULTI_THUMBNAILS,
            cls.VIDEO_BYTES,
        ):
            st.session_state[key] = None
        st.session_state[cls.PIPELINE_PROGRESS] = PipelineProgress()
        st.session_state[cls.PIPELINE_EXECUTED] = False

    @classmethod
    def ensure_collected_data(cls) -> dict:
        """수집 데이터가 dict 형태이도록 보장."""
        current = cls.get(cls.COLLECTED_DATA)
        if current is None:
            current = {}
        elif hasattr(current, "model_dump"):
            current = current.model_dump()
        elif not isinstance(current, dict):
            current = current.__dict__

        cls.set(cls.COLLECTED_DATA, current)
        return current

    @classmethod
    def set_collected_section(cls, key: str, value: dict) -> None:
        """수집 데이터 섹션 업데이트."""
        data = cls.ensure_collected_data()
        data[key] = value
        cls.set(cls.COLLECTED_DATA, data)

    @classmethod
    def set_pipeline_result(cls, result) -> None:
        """파이프라인 결과를 세션에 저장."""
        if getattr(result, "collected_data", None) is not None:
            cls.set(cls.COLLECTED_DATA, result.collected_data)
        if getattr(result, "strategy", None):
            cls.set(cls.PIPELINE_STRATEGY, result.strategy)
        if getattr(result, "generated_content", None):
            gen = result.generated_content
            if getattr(gen, "thumbnail_data", None):
                cls.set(cls.GENERATED_THUMBNAIL, gen.thumbnail_data)
            if getattr(gen, "thumbnail_url", None):
                cls.set(cls.GENERATED_THUMBNAIL_URL, gen.thumbnail_url)
            if getattr(gen, "video_url", None):
                cls.set(cls.GENERATED_VIDEO, gen.video_url)
                cls.set(cls.GENERATED_VIDEO_URL, gen.video_url)
            if getattr(gen, "multi_thumbnails", None):
                cls.set(cls.MULTI_THUMBNAILS, gen.multi_thumbnails)
            if getattr(gen, "video_bytes", None):
                cls.set(cls.VIDEO_BYTES, gen.video_bytes)

        cls.set(cls.PIPELINE_EXECUTED, True)

    @classmethod
    def get_selected_product(cls) -> Optional[dict]:
        """선택된 상품 반환."""
        return cls.get(cls.SELECTED_PRODUCT)

    @classmethod
    def set_selected_product(cls, product: Any) -> None:
        """선택된 상품 설정."""
        cls.set(cls.SELECTED_PRODUCT, product)

    @classmethod
    def get_collected_data(cls) -> Optional[dict]:
        """수집 데이터 반환."""
        return cls.get(cls.COLLECTED_DATA)

    @classmethod
    def set_collected_data(cls, data: dict) -> None:
        """수집 데이터 설정."""
        cls.set(cls.COLLECTED_DATA, data)

    @classmethod
    def get_pipeline_progress(cls) -> PipelineProgress:
        """파이프라인 진행 상태 반환."""
        return cls.get(cls.PIPELINE_PROGRESS, PipelineProgress())

    @classmethod
    def update_pipeline_progress(cls, step: PipelineStep, message: str = "") -> None:
        """파이프라인 진행 상태 업데이트."""
        progress = cls.get_pipeline_progress()
        progress.update(step, message)
        cls.set(cls.PIPELINE_PROGRESS, progress)

    @classmethod
    def get_pipeline_config(cls) -> PipelineConfig:
        """파이프라인 설정 반환."""
        return cls.get(cls.PIPELINE_CONFIG, PipelineConfig())

    @classmethod
    def set_pipeline_config(cls, config: PipelineConfig) -> None:
        """파이프라인 설정 저장."""
        cls.set(cls.PIPELINE_CONFIG, config)

    @classmethod
    def has_collected_data(cls) -> bool:
        """수집 데이터 존재 여부."""
        return cls.get(cls.COLLECTED_DATA) is not None

    @classmethod
    def has_strategy(cls) -> bool:
        """전략 생성 여부."""
        return cls.get(cls.PIPELINE_STRATEGY) is not None
