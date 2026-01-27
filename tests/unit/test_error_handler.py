import unittest
from unittest.mock import patch

from genesis_ai.core.exceptions import ErrorCode, GenesisError
from genesis_ai.utils.error_handler import ErrorMessageMapper, handle_error, safe_action


class TestErrorHandler(unittest.TestCase):
    """에러 핸들링 유틸리티 테스트"""

    def test_message_mapper_keyword_match(self):
        """1. 키워드 기반 메시지 매핑 테스트"""
        # Quota 에러 (문자열 포함 여부 확인)
        quota_err = Exception("Your project has exceeded the daily quota limit.")
        msg = ErrorMessageMapper.get_message(quota_err)
        self.assertIn("API 사용량이 초과되었습니다", msg)

        # Rate check
        rate_err = Exception("Rate limit exceeded")
        msg = ErrorMessageMapper.get_message(rate_err)
        self.assertIn("요청 빈도가 너무 높습니다", msg)

    def test_message_mapper_type_match(self):
        """2. 예외 타입 기반 메시지 매핑 테스트"""
        # ValueError
        msg = ErrorMessageMapper.get_message(ValueError("Invalid input"))
        self.assertIn("입력된 값이 올바르지 않습니다", msg)

        # KeyError
        msg = ErrorMessageMapper.get_message(KeyError("missing_field"))
        self.assertIn("필요한 데이터 필드가 누락되었습니다", msg)

    def test_message_mapper_default(self):
        """3. 매핑되지 않은 일반 예외 테스트"""
        # 일반 Exception
        err = Exception("Unknown error occurred")
        msg = ErrorMessageMapper.get_message(err, context="테스트")
        self.assertIn("예상치 못한 오류가 발생했습니다", msg)
        self.assertIn("테스트", msg)

    def test_message_mapper_genesis_error(self):
        """GenesisError 메시지 우선 사용"""
        err = GenesisError(code=ErrorCode.NETWORK_ERROR)
        msg = ErrorMessageMapper.get_message(err, context="테스트")
        self.assertIn("테스트 실패", msg)
        self.assertIn("네트워크 연결", msg)

    @patch("genesis_ai.utils.error_handler.log_error")
    def test_handle_error_logging(self, mock_log):
        """4. handle_error 함수가 로그를 남기는지 테스트"""
        handle_error(ValueError("Test Error"), context="LogTest")
        mock_log.assert_called_once()
        # 로그 메시지에 에러 내용이 포함되어야 함
        args, _ = mock_log.call_args
        self.assertIn("Test Error", args[0])

    @patch("genesis_ai.utils.error_handler.st")
    @patch("genesis_ai.utils.error_handler.log_error")
    def test_safe_action_decorator_success(self, mock_log, mock_st):
        """5. safe_action 데코레이터 - 성공 케이스"""

        @safe_action(context="성공함수")
        def success_func():
            return "Success"

        result = success_func()

        self.assertEqual(result, "Success")
        mock_st.error.assert_not_called()
        mock_log.assert_not_called()

    @patch("genesis_ai.utils.error_handler.st")
    @patch("genesis_ai.utils.error_handler.log_error")
    def test_safe_action_decorator_failure(self, mock_log, mock_st):
        """6. safe_action 데코레이터 - 실패 케이스"""

        @safe_action(context="실패함수")
        def fail_func():
            raise ValueError("Something went wrong")

        result = fail_func()

        # 예외 발생 시 None 반환
        self.assertIsNone(result)

        # 로그 기록 및 st.error 호출 확인
        mock_log.assert_called_once()
        mock_st.error.assert_called_once()

        # 에러 메시지에 '실패함수' 컨텍스트와 '입력된 값' 등의 매핑 메시지가 있어야 함
        args, _ = mock_st.error.call_args
        self.assertIn("실패함수 실패", args[0])
        self.assertIn("입력된 값이 올바르지 않습니다", args[0])


if __name__ == "__main__":
    unittest.main()
