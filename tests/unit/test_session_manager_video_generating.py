import streamlit as st

from genesis_ai.presentation.state.session_manager import SessionManager


def test_init_session_state_sets_video_generating_flag():
    st.session_state.clear()
    SessionManager.init_session_state()
    assert SessionManager.get(SessionManager.VIDEO_GENERATING) is False


def test_reset_pipeline_state_resets_video_generating_flag():
    st.session_state.clear()
    SessionManager.init_session_state()
    SessionManager.set(SessionManager.VIDEO_GENERATING, True)
    SessionManager.reset_pipeline_state()
    assert SessionManager.get(SessionManager.VIDEO_GENERATING) is False
