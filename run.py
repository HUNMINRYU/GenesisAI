#!/usr/bin/env python
"""
Genesis AI Studio 실행 스크립트
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Streamlit 앱 실행"""
    project_root = Path(__file__).parent
    app_path = project_root / "src" / "genesis_ai" / "presentation" / "app.py"
    src_path = project_root / "src"

    if not app_path.exists():
        print(f"앱 파일을 찾을 수 없습니다: {app_path}")
        sys.exit(1)

    # PYTHONPATH에 src 디렉토리 추가 (상대 임포트 문제 해결)
    env = os.environ.copy()
    python_path = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        f"{src_path}{os.pathsep}{python_path}" if python_path else str(src_path)
    )

    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    subprocess.run(cmd, env=env)


if __name__ == "__main__":
    main()
