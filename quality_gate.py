#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
품질 게이트 스크립트
모든 변경 후 실행하여 안정성을 검증합니다.
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Windows 콘솔 인코딩 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_command(cmd: list[str], description: str) -> tuple[bool, str]:
    """명령어 실행 및 결과 반환"""
    print(f"\n{'=' * 50}")
    print(f"[CHECK] {description}")
    print(f"{'=' * 50}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print("[PASS] 통과")
            return True, result.stdout
        else:
            print("[FAIL] 실패")
            print(result.stderr or result.stdout)
            return False, result.stderr or result.stdout

    except subprocess.TimeoutExpired:
        print("[TIMEOUT] 시간 초과")
        return False, "Timeout"
    except Exception as e:
        print(f"[ERROR] 오류: {e}")
        return False, str(e)


def main():
    """품질 게이트 실행"""
    print("\n" + "=" * 60)
    print("[QUALITY GATE] GENESIS AI STUDIO - 품질 게이트")
    print("=" * 60)
    print(f"[TIME] 실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    project_root = Path(__file__).parent
    src_path = project_root / "src"

    # 품질 검증 단계
    gates = [
        (["python", "tests/test_smoke.py"], "스모크 테스트"),
        (
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0, 'src'); from genesis_ai.config.settings import get_settings; print('Settings OK')",
            ],
            "설정 로드",
        ),
        (
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0, 'src'); from genesis_ai.utils.cache import TTLCache; print('Cache OK')",
            ],
            "캐시 모듈",
        ),
        (
            [
                "python",
                "-c",
                "import sys; sys.path.insert(0, 'src'); from genesis_ai.core.exceptions import GenesisError; print('Exceptions OK')",
            ],
            "예외 모듈",
        ),
    ]

    results = []

    for cmd, description in gates:
        passed, output = run_command(cmd, description)
        results.append((description, passed, output))

    # 결과 요약
    print("\n" + "=" * 60)
    print("[RESULT] 품질 게이트 결과")
    print("=" * 60)

    passed_count = sum(1 for _, passed, _ in results if passed)
    total_count = len(results)

    for description, passed, _ in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status}: {description}")

    print(f"\n  총 {passed_count}/{total_count} 통과")

    # 결과 기록
    log_file = project_root / "quality_gate.log"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n{'=' * 60}\n")
        f.write(f"실행 시간: {datetime.now().isoformat()}\n")
        f.write(f"결과: {passed_count}/{total_count} 통과\n")
        for description, passed, output in results:
            status = "PASS" if passed else "FAIL"
            f.write(f"  [{status}] {description}\n")
            if not passed:
                f.write(f"    원인: {output[:200]}\n")

    print(f"\n[LOG] 결과가 {log_file}에 기록되었습니다.")

    # 실패 시 종료 코드 1
    if passed_count < total_count:
        print("\n[WARNING] 품질 게이트 실패! 변경 사항을 검토하세요.")
        sys.exit(1)
    else:
        print("\n[SUCCESS] 모든 품질 게이트 통과!")
        sys.exit(0)


if __name__ == "__main__":
    main()
