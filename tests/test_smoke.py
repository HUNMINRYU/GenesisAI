# -*- coding: utf-8 -*-
"""
핵심 기능 테스트 (Smoke Test)
앱의 핵심 기능이 정상 동작하는지 검증합니다.
"""

import sys
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# PYTHONPATH 설정
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def test_imports():
    """모든 핵심 모듈 import 테스트"""
    print("=" * 50)
    print("TEST: 핵심 모듈 import")
    print("=" * 50)

    modules = [
        ("genesis_ai.config.settings", "get_settings"),
        ("genesis_ai.config.dependencies", "get_services"),
        ("genesis_ai.services.youtube_service", "YouTubeService"),
        ("genesis_ai.services.naver_service", "NaverService"),
        ("genesis_ai.utils.cache", "TTLCache"),
        ("genesis_ai.core.exceptions", "GenesisError"),
    ]

    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  [PASS] {module_name}.{class_name}")
        except Exception as e:
            print(f"  [FAIL] {module_name}.{class_name}: {e}")
            raise


def test_cache():
    """캐시 기능 테스트"""
    print("\n" + "=" * 50)
    print("TEST: TTL 캐시 기능")
    print("=" * 50)

    from genesis_ai.utils.cache import TTLCache

    cache = TTLCache(default_ttl=60)

    # 저장 테스트
    cache.set("test_key", {"data": "test_value"})
    result = cache.get("test_key")

    assert result and result["data"] == "test_value"
    print("  [PASS] 캐시 저장/조회 성공")


def test_exceptions():
    """예외 클래스 테스트"""
    print("\n" + "=" * 50)
    print("TEST: 예외 처리 시스템")
    print("=" * 50)

    from genesis_ai.core.exceptions import (
        ErrorCode,
        classify_error,
    )

    # 에러 분류 테스트
    test_error = Exception("connection timeout")
    classified = classify_error(test_error)

    assert classified.code == ErrorCode.NETWORK_ERROR
    print("  [PASS] 에러 분류 정상 (timeout → NETWORK_ERROR)")


def run_all_tests():
    """모든 테스트 실행"""
    print("\n[TEST] Genesis AI Studio - Smoke Test")
    print("=" * 50)

    tests = [
        ("Import 테스트", test_imports),
        ("캐시 테스트", test_cache),
        ("예외 처리 테스트", test_exceptions),
    ]

    results = []
    for name, test_func in tests:
        try:
            test_func()
            results.append(True)
        except Exception as e:
            print(f"\n  [FAIL] {name} 실패: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("[RESULT] 결과 요약")
    print("=" * 50)

    passed = sum(results)
    total = len(results)

    for i, (name, _) in enumerate(tests):
        status = "[PASS] PASS" if results[i] else "[FAIL] FAIL"
        print(f"  {status}: {name}")

    print(f"\n  총 {passed}/{total} 통과")

    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
