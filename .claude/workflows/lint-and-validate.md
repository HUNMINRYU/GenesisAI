---
description: 자동 품질 관리 - 모든 코드 수정 후 실행
---

# 린트 및 검증 (Lint and Validate)

**목표**: 작업을 완료하기 전에 코드가 오류 없이 표준을 준수하는지 확인합니다.

## 절차

### 1. 생태계 식별
*   **Python**: `requirements.txt`, `pyproject.toml`, 또는 `.py` 파일을 확인합니다.
*   **Node/TS**: `package.json`을 확인합니다.

### 2. 검증 도구 실행
표준 린터 실행에 대해 **허락을 구하지 마십시오**. 선제적으로 실행하십시오.

#### Python
*   **Linter**: `ruff check . --fix` (설치된 경우) 또는 `flake8 .`
*   **Tests**: `pytest` 또는 `python -m pytest`
*   **Type Check**: `mypy .` (Strict typing이 적용된 경우)

#### Node/TS
*   **Lint**: `npm run lint`
*   **Types**: `npx tsc --noEmit`
*   **Test**: `npm test`

### 3. 분석 및 수정
*   **출력 확인**: 모든 경고/오류를 캡처합니다.
*   **즉시 수정**: 문법 오류, 정의되지 않은 변수, 사용되지 않는 import 등은 즉시 수정합니다.
*   **복잡한 문제**: 수정에 로직 변경이 필요한 경우 사용자에게 확인합니다.
*   **재실행**: 완료하기 전에 출력이 깨끗한지 확인합니다.

> **규칙**: 린터와 기본적인 테스트를 통과하기 전까지 코드는 "완료"된 것이 아닙니다.
