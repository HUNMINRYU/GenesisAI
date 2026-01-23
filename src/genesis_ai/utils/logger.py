"""
로깅 유틸리티
앱 전체 로깅 시스템
"""
import functools
import logging
import sys
from datetime import datetime
from typing import Callable


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터"""

    COLORS = {
        "DEBUG": "\033[36m",    # Cyan
        "INFO": "\033[32m",     # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",    # Red
        "CRITICAL": "\033[35m", # Magenta
    }
    RESET = "\033[0m"

    EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "📌",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        emoji = self.EMOJIS.get(record.levelname, "📋")
        record.emoji = emoji
        record.color = color
        record.reset = self.RESET
        return super().format(record)


def setup_logger(name: str = "genesis_ai", level: int = logging.DEBUG) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 기존 핸들러 제거
    logger.handlers.clear()

    # 콘솔 핸들러
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)

    # 포맷터
    formatter = ColoredFormatter(
        "%(emoji)s [%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.propagate = False

    return logger


# 기본 앱 로거
_app_logger: logging.Logger | None = None


def get_logger(name: str = "genesis_ai") -> logging.Logger:
    """로거 인스턴스 반환"""
    global _app_logger
    if _app_logger is None:
        _app_logger = setup_logger(name)
    return _app_logger


# 단축 함수들
def log_step(step_name: str, status: str = "시작") -> None:
    """단계 로그"""
    get_logger().info(f"[STEP] {step_name} - {status}")


def log_info(message: str) -> None:
    """정보 로그"""
    get_logger().info(message)


def log_debug(message: str) -> None:
    """디버그 로그"""
    get_logger().debug(message)


def log_warning(message: str) -> None:
    """경고 로그"""
    get_logger().warning(message)


def log_error(message: str) -> None:
    """에러 로그"""
    get_logger().error(message)


def log_success(message: str) -> None:
    """성공 로그"""
    get_logger().info(f"✅ {message}")


def log_api_call(api_name: str, endpoint: str = "", status: str = "호출") -> None:
    """API 호출 로그"""
    get_logger().info(f"[API] {api_name} {endpoint} - {status}")


def log_timing(operation: str, duration_ms: float) -> None:
    """타이밍 로그"""
    get_logger().info(f"[TIMING] {operation}: {duration_ms:.2f}ms")


def log_tab_load(tab_name: str) -> None:
    """탭 로드 로그"""
    get_logger().info(f"[TAB] {tab_name} 탭 로드됨")


def log_user_action(action: str, details: str = "") -> None:
    """사용자 액션 로그"""
    get_logger().info(f"[USER] {action} {details}")


def log_data(data_type: str, count: int = 0) -> None:
    """데이터 로그"""
    get_logger().debug(f"[DATA] {data_type}: {count}개")


def log_function(func_name: str | None = None) -> Callable:
    """함수 로깅 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            log_step(name, "시작")
            try:
                result = func(*args, **kwargs)
                log_step(name, "완료")
                return result
            except Exception as e:
                log_error(f"{name} 실패: {e}")
                raise

        return wrapper

    return decorator


def log_app_start() -> None:
    """앱 시작 로그"""
    print("\n" + "=" * 50)
    print("🚀 Genesis AI Studio 시작")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50 + "\n")


def log_app_ready() -> None:
    """앱 준비 완료 로그"""
    print("\n" + "=" * 50)
    print("✅ 대시보드 준비 완료")
    print("=" * 50 + "\n")
