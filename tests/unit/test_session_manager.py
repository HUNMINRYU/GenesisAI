import sys
import types
from pathlib import Path

import pytest
import streamlit as st

presentation_module = types.ModuleType("genesis_ai.presentation")
presentation_module.__path__ = [
    str(Path(__file__).resolve().parents[2] / "src" / "genesis_ai" / "presentation")
]
sys.modules.setdefault("genesis_ai.presentation", presentation_module)

from genesis_ai.presentation.state.session_manager import SessionManager  # noqa: E402


@pytest.fixture
def session_state(monkeypatch):
    state = {}
    monkeypatch.setattr(st, "session_state", state, raising=False)
    return state


def test_init_session_state_includes_error_logs(session_state):
    SessionManager.init_session_state()
    assert SessionManager.get(SessionManager.PIPELINE_ERROR_LOGS) == []


def test_reset_pipeline_state_clears_error_logs(session_state):
    SessionManager.init_session_state()
    SessionManager.set(SessionManager.PIPELINE_ERROR_LOGS, [{"msg": "err"}])
    SessionManager.reset_pipeline_state()
    assert SessionManager.get(SessionManager.PIPELINE_ERROR_LOGS) == []
