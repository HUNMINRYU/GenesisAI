"""
터미널 스타일 로그 뷰어 컴포넌트
"""

import re

import streamlit as st

from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.utils.logger import add_log_callback

# 세션 키 상수
LOG_SESSION_KEY = "global_logs"
MAX_LOG_LINES = 500


def _parse_log_line(msg: str) -> dict:
    """로그 라인을 파싱하여 구조화된 데이터 반환"""
    # ANSI 색상 코드 제거
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    clean_msg = ansi_escape.sub("", msg)

    # 패턴: 📌 [HH:MM:SS] LEVEL - 메시지
    pattern = r"^(.+?)\s*\[(\d{2}:\d{2}:\d{2})\]\s*(\w+)\s*-\s*(.*)$"
    match = re.match(pattern, clean_msg)

    if match:
        emoji, timestamp, level, message = match.groups()
        return {
            "emoji": emoji.strip(),
            "timestamp": timestamp,
            "level": level.upper(),
            "message": message,
            "raw": clean_msg,
        }
    return {
        "emoji": "",
        "timestamp": "",
        "level": "INFO",
        "message": clean_msg,
        "raw": clean_msg,
    }


def _log_handler(msg: str) -> None:
    """로그 콜백 핸들러 - 전역 세션 로그에 추가"""
    logs = SessionManager.get(LOG_SESSION_KEY) or []

    parsed = _parse_log_line(msg)
    logs.append(parsed)

    # 최대 라인 수 유지
    if len(logs) > MAX_LOG_LINES:
        logs = logs[-MAX_LOG_LINES:]

    SessionManager.set(LOG_SESSION_KEY, logs)


def setup_global_logging() -> None:
    """앱 시작 시 전역 로깅 설정"""
    add_log_callback(_log_handler)


def _format_log_html(log: dict) -> str:
    """단일 로그 라인을 HTML로 포맷"""
    level = log.get("level", "INFO").lower()
    level_class = f"log-level-{level}"

    emoji = log.get("emoji", "")
    timestamp = log.get("timestamp", "")
    message = log.get("message", "")

    # timestamp가 있으면 표시, 없으면 raw 메시지
    if timestamp:
        level_text = log.get("level", "INFO")
        return (
            f'<div class="log-line">'
            f'<span class="log-emoji">{emoji}</span> '
            f'<span class="log-timestamp">[{timestamp}]</span> '
            f'<span class="{level_class}">{level_text}</span> '
            f'<span class="log-message">- {message}</span>'
            f"</div>"
        )
    else:
        raw_msg = log.get("raw", message)
        return f'<div class="log-line"><span class="log-message">{raw_msg}</span></div>'


def _build_terminal_html(logs: list[dict], title: str, height: int) -> str:
    """터미널 HTML 구조 생성"""
    # 로그 HTML 생성
    if logs:
        log_html = "\n".join(_format_log_html(log) for log in logs)
    else:
        log_html = '<div class="log-line log-empty">로그가 없습니다...</div>'

    return f"""
    <div class="terminal-container" style="height: {height}px;">
        <div class="terminal-header">
            <div class="terminal-dots">
                <div class="terminal-dot red"></div>
                <div class="terminal-dot yellow"></div>
                <div class="terminal-dot green"></div>
            </div>
            <span class="terminal-title">{title}</span>
        </div>
        <div class="terminal-body">
            {log_html}
        </div>
    </div>
    """


def render_terminal_log_viewer(
    title: str = "System Logs",
    height: int = 400,
    show_clear_button: bool = True,
    key_suffix: str = "",
) -> None:
    """터미널 스타일 로그 뷰어 렌더링"""
    logs = SessionManager.get(LOG_SESSION_KEY) or []

    terminal_html = _build_terminal_html(logs, title, height)
    st.markdown(terminal_html, unsafe_allow_html=True)

    # 컨트롤 버튼
    if show_clear_button:
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("🗑️ 로그 비우기", key=f"clear_logs_{key_suffix}"):
                SessionManager.set(LOG_SESSION_KEY, [])
                st.rerun()
        with col2:
            st.caption(f"총 {len(logs)}줄")


def render_inline_terminal(
    container,
    logs: list[dict],
    title: str = "Pipeline Execution Log",
    height: int = 350,
) -> None:
    """인라인 터미널 뷰어 (st.empty 컨테이너용)"""
    terminal_html = _build_terminal_html(logs, title, height)
    container.markdown(terminal_html, unsafe_allow_html=True)


def render_log_viewer() -> None:
    """전역 로그 뷰어 렌더링 (기존 호환성 유지)"""
    logs = SessionManager.get(LOG_SESSION_KEY) or []

    with st.expander("📜 시스템 실행 로그 (System Logs)", expanded=bool(logs)):
        if logs:
            render_terminal_log_viewer(
                title="System Logs",
                height=350,
                show_clear_button=True,
                key_suffix="global",
            )
        else:
            st.caption("아직 기록된 실행 로그가 없습니다.")
