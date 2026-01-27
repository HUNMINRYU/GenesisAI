"""
로깅 유틸리티
앱 전체 로깅 시스템
"""

import functools
import io
import logging
import sys
from typing import Callable


class ColoredFormatter(logging.Formatter):
    """컬러 로그 포맷터"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
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


# 기본 앱 로거
_app_logger: logging.Logger | None = None
_log_callbacks: list[Callable[[str], None]] = []


class CallbackHandler(logging.Handler):
    """로그 콜백 핸들러 - 로그를 Streamlit 세션 등에 전달하기 위함"""

    def __init__(self, level=logging.NOTSET):
        super().__init__(level)
        self.formatter = ColoredFormatter(
            "%(emoji)s [%(asctime)s] %(levelname)s - %(message)s",
            datefmt="%H:%M:%S",
        )

    def emit(self, record):
        try:
            msg = self.format(record)
            for callback in _log_callbacks:
                try:
                    callback(msg)
                except Exception:
                    pass  # 콜백 에러 무시
        except Exception:
            self.handleError(record)


def add_log_callback(callback: Callable[[str], None]) -> None:
    """로그 콜백 추가"""
    if callback not in _log_callbacks:
        _log_callbacks.append(callback)


def clear_log_callbacks() -> None:
    """로그 콜백 초기화"""
    _log_callbacks.clear()


def setup_logger(
    name: str = "genesis_ai", level: int = logging.DEBUG
) -> logging.Logger:
    """로거 설정"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 기존 핸들러 제거
    logger.handlers.clear()

    # 콘솔 핸들러
    console_stream = sys.stdout
    try:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        console_stream = io.TextIOWrapper(
            sys.stdout.buffer, encoding=encoding, errors="replace"
        )
    except Exception:
        pass

    console_handler = logging.StreamHandler(console_stream)
    console_handler.setLevel(level)

    # 포맷터
    formatter = ColoredFormatter(
        "%(emoji)s [%(asctime)s] %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    # 콜백 핸들러 (INFO 이상만 전달, 너무 시끄러운 DEBUG 제외)
    callback_handler = CallbackHandler(logging.INFO)
    callback_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(callback_handler)
    logger.propagate = False

    return logger


def get_logger(name: str = "genesis_ai") -> logging.Logger:
    """로거 인스턴스 반환"""
    global _app_logger
    if _app_logger is None:
        _app_logger = setup_logger(name)
    return _app_logger


# 단축 함수들


# 단축 함수들
def log_section(title: str) -> None:
    """섹션 시작 로그 (구분선 포함)"""
    get_logger().info(f"\n{'=' * 50}")
    get_logger().info(f"🚀 {title}")
    get_logger().info(f"{'=' * 50}")


def log_app_start() -> None:
    """앱 시작 로그"""
    log_section("제네시스코리아 스튜디오 시작")


def log_app_ready() -> None:
    """앱 준비 완료 로그"""
    log_success("제네시스코리아 스튜디오 준비 완료")


def log_step(step_name: str, status: str = "시작", details: str = "") -> None:
    """단계 로그"""
    msg = f"[STEP] {step_name} - {status}"
    if details:
        msg += f" ({details})"
    get_logger().info(msg)


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
    """API 호출 로그 (간단)"""
    get_logger().info(f"[API] {api_name} {endpoint} - {status}")


def log_api_start(api_name: str, details: str = "") -> None:
    """API 호출 시작"""
    get_logger().info(f"📡 [API] {api_name} 요청 시작... {details}")


def log_api_end(api_name: str, duration: float = 0, items: int = 0) -> None:
    """API 호출 완료"""
    msg = f"✅ [API] {api_name} 응답 완료 ({duration:.2f}s)"
    if items > 0:
        msg += f" - {items}개 항목 수집"
    get_logger().info(msg)


def log_process(task: str, current: int, total: int) -> None:
    """진행 상황 로그"""
    percent = int((current / total) * 100)
    bar = "█" * (percent // 10) + "░" * (10 - (percent // 10))
    get_logger().info(f"⏳ [PROCESS] {task}: {bar} {percent}%")


def log_timing(operation: str, duration_ms: float) -> None:
    """타이밍 로그"""
    get_logger().info(f"⏱️ [TIMING] {operation}: {duration_ms:.2f}ms")


def log_tab_load(tab_name: str) -> None:
    """탭 로드 로그"""
    get_logger().info(f"📌 [TAB] {tab_name} 탭 로드됨")


def log_user_action(action: str, details: str = "") -> None:
    """사용자 액션 로그"""
    get_logger().info(f"👤 [USER] {action} {details}")


def log_data(data_type: str, count: int = 0, source: str = "") -> None:
    """데이터 로그"""
    src_str = f" from {source}" if source else ""
    get_logger().info(f"📦 [DATA] {data_type}: {count}개{src_str}")


def log_function(func_name: str | None = None) -> Callable:
    """함수 로깅 데코레이터"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            # log_step(name, "시작") # 너무 시끄러울 수 있어서 디버그로 변경
            get_logger().debug(f"[FUNC] {name} 시작")
            try:
                result = func(*args, **kwargs)
                get_logger().debug(f"[FUNC] {name} 완료")
                return result
            except Exception as e:
                log_error(f"{name} 실패: {e}")
                raise

        return wrapper

    return decorator


class PipelineLogger:
    """
    파이프라인 실행 로거 (Context Manager)
    사용 예:
    with PipelineLogger("Veo 3.1 프롬프트 생성") as logger:
        logger.log("썸네일 타입", "공포형")
        logger.step(1, 3, "썸네일 이미지 분석 중...")
        logger.success("완료!")
    """

    def __init__(self, title: str):
        self.title = title

    def __enter__(self):
        print(f"{'=' * 50}")
        print(f"[STEP] {self.title} 시작")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f"{'=' * 50}")
        if exc_type:
            print(f"[ERROR] 오류 발생: {exc_val}")
        # 예외를 억제하지 않음

    def log(self, key: str, value: str):
        """키-값 정보 로깅"""
        print(f"   - {key}: {value}")

    def step(self, current: int, total: int, message: str):
        """진행 단계 로깅"""
        print(f"   [{current}/{total}] {message}")

    def success(self, message: str):
        """성공 메시지"""
        print(f"[OK] {message}")
