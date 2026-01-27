"""Media rendering helpers for Streamlit."""

from __future__ import annotations

import io
import os
from typing import Any

import streamlit as st


def render_video(video_value: Any, *, format: str | None = None) -> None:
    """Render videos safely across URL/path/bytes inputs."""
    resolved_format = format or "video/mp4"
    if video_value is None:
        return

    if isinstance(video_value, (bytes, bytearray)):
        st.video(io.BytesIO(video_value), format=resolved_format)
        return

    if hasattr(video_value, "read"):
        if format:
            st.video(video_value, format=format)
        else:
            st.video(video_value, format=resolved_format)
        return

    if isinstance(video_value, str):
        value = video_value.strip()
        if value.startswith("b'") or value.startswith('b"'):
            st.error("비디오 값이 bytes 문자열로 전달되었습니다. bytes 그대로 전달해주세요.")
            return

        if value.startswith(("http://", "https://", "gs://")):
            st.video(value)
            return

        if os.path.exists(value):
            st.video(value)
            return

        st.error(f"비디오 경로/URL이 유효하지 않습니다: {value}")
        return

    st.error(f"지원하지 않는 비디오 타입: {type(video_value)}")
