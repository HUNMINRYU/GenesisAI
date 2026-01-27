"""
제네시스코리아 - 에러 핸들링 유틸리티
"""

import functools
import traceback
from typing import Callable, Dict, Optional, Type

import streamlit as st

from genesis_ai.core.exceptions import GenesisError

from .logger import log_error


class ErrorMessageMapper:
    """예외 타입과 메시지를 사용자 친화적인 한국어 메시지로 매핑"""

    # 예외 타입별 기본 메시지
    TYPE_MAP: Dict[Type[Exception], str] = {
        ValueError: "입력된 값이 올바르지 않습니다. 다시 확인해주세요.",
        KeyError: "필요한 데이터 필드가 누락되었습니다. 데이터를 다시 수집해주세요.",
        ConnectionError: "서버와 연결할 수 없습니다. 인터넷 상태를 확인해주세요.",
        TimeoutError: "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요.",
        PermissionError: "권한이 없습니다. API 키 설정이나 권한을 확인해주세요.",
        FileNotFoundError: "요청하신 파일을 찾을 수 없습니다.",
    }

    # 특정 에러 메시지 키워드별 매핑 (부분 일치)
    KEYWORD_MAP = {
        "quota": "API 사용량이 초과되었습니다 (Quota Exceeded). 관리자에게 문의하세요.",
        "rate limit": "요청 빈도가 너무 높습니다 (Rate Limit). 잠시 후 다시 시도해주세요.",
        "unauthorized": "인증에 실패했습니다. API 키가 올바른지 확인해주세요.",
        "not found": "요청한 리소스를 찾을 수 없습니다.",
        "json": "데이터 형식이 올바르지 않습니다 (JSON Parse Error).",
    }

    @classmethod
    def get_message(cls, exception: Exception, context: str = "") -> str:
        """예외 객체를 받아 사용자 친화적인 메시지로 변환"""
        error_str = str(exception).lower()

        # GenesisError는 자체 메시지/힌트를 우선 사용
        if isinstance(exception, GenesisError):
            base = exception.get_full_message()
            return f"{context} 실패: {base}" if context else base

        # 1. 키워드 매칭 (우선순위 높음)
        for keyword, msg in cls.KEYWORD_MAP.items():
            if keyword in error_str:
                return f"{context} 중 문제가 발생했습니다: {msg}"

        # 2. 예외 타입 매칭
        for exc_type, msg in cls.TYPE_MAP.items():
            if isinstance(exception, exc_type):
                return f"{context} 실패: {msg}"

        # 3. 기본 메시지
        return f"{context} 중 예상치 못한 오류가 발생했습니다: {exception}"


def handle_error(e: Exception, context: str = "작업") -> str:
    """
    예외를 처리하고 사용자 메시지를 반환합니다. 로그도 함께 기록합니다.
    """
    user_message = ErrorMessageMapper.get_message(e, context)

    # 상세 로그 기록
    log_msg = f"[{context}] {str(e)}\n{traceback.format_exc()}"
    log_error(log_msg)

    return user_message


def safe_action(
    context: str, error_message: Optional[str] = None, reraise: bool = False
):
    """
    Streamlit 액션을 안전하게 감싸는 데코레이터

    Args:
        context: 에러 발생 시 표시할 컨텍스트 (예: '유튜브 검색')
        error_message: 커스텀 에러 메시지 (없으면 자동 생성)
        reraise: 에러 로그 기록 후 다시 발생시킬지 여부
    """

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                msg = error_message or handle_error(e, context)

                # Streamlit UI에 에러 표시 (함수 실행 중 st 컨텍스트가 있다고 가정)
                try:
                    st.error(msg)
                    if isinstance(e, GenesisError) and e.hint:
                        st.caption(e.hint)
                    elif hasattr(e, "help_msg"):  # 커스텀 예외에 도움말이 있다면 표시
                        st.caption(f"💡 {e.help_msg}")
                    elif "quota" in str(e).lower():
                        st.caption(
                            "💡 일일 할당량이 소진되었을 수 있습니다. 내일 다시 시도해주세요."
                        )
                except Exception as ui_error:
                    log_error(
                        f"[{context}] UI 에러 표시 실패: {ui_error}"
                    )

                if reraise:
                    raise e
                return None

        return wrapper

    return decorator
