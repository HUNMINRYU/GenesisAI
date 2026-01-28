# 🏗️ 프로젝트 구조 및 코드 분석 보고서

## 1. 개요
본 문서는 `genesis-ai-wt/gemini` 프로젝트의 현재 디렉토리 구조, 코드 구성, 그리고 `RULES.md` 및 `README.md`와의 일치 여부를 분석한 결과입니다.

## 2. 프로젝트 구조 분석

### 2.1 루트 디렉토리
- **핵심 파일**: `README.md`, `GUARDRAILS.md`, `pyproject.toml`
- **상태**: 문서화 및 설정이 잘 관리되고 있음. `pyproject.toml`을 통해 최신 Python 표준 패키징 방식을 따름.

### 2.2 소스 코드 (`src/genesis_ai`)
`README.md`에 명시된 구조와 실제 구조 간에 일부 차이가 존재함.

| 디렉토리         | 역할               | 비고                                                                                                                                                    |
| :--------------- | :----------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `config`         | 설정 관리          | -                                                                                                                                                       |
| `core`           | 핵심 도메인/엔티티 | -                                                                                                                                                       |
| `infrastructure` | 외부 어댑터        | Gemini, YouTube, Naver 등                                                                                                                               |
| `presentation`   | UI/UX (Streamlit)  | `app.py`, `tabs/`, `components/` 등 구조화 잘됨                                                                                                         |
| `services`       | 비즈니스 로직      | `pipeline/` 및 기능별 서비스 파일 분리 잘됨                                                                                                             |
| `utils`          | 공통 유틸리티      | **README 미기재**. `logger`, `error_handler`, `cache` 등 중요 기능 포함                                                                                 |
| `api`            | 유틸리티/래퍼      | **README 미기재**. REST API가 아님. `retry`, `json validation`, `hook generation` 등 내부 로직을 위한 헬퍼 함수 모음. 이름 변경(`helpers` 등) 고려 필요 |

### 2.3 테스트 (`tests`)
- **Unit Test**: `tests/unit`에 주요 서비스(`pipeline`, `video`, `analysis` 등)에 대한 테스트 코드가 존재함.
- **Integration Test**: `tests/integration`에 `test_smoke.py` 등 제한적으로 존재.
- **커버리지**: 주요 비즈니스 로직에 대한 단위 테스트 커버리지는 양호해 보임.

### 2.4 문서 (`docs`)
- `analysis`: 최적화 전략 등 아키텍처 문서 존재.
- `triage`: 버그 및 트러블슈팅 문서가 체계적으로 관리되고 있음 (`mediafilestorageerror.md` 등).

## 3. 주요 발견 사항 및 개선 제안

### 3.1 `api` 디렉토리의 모호성
- **현황**: `src/genesis_ai/api/__init__.py` 파일 하나만 존재함.
- **분석**: Streamlit 앱이므로 별도의 REST API 엔드포인트가 불필요할 수 있음. 만약 내부 로직 호출용이라면 위치나 이름이 부적절할 수 있음. 코드 내용 확인 결과, 단순한 노출용 파일인지 실제 라우팅인지 확인 필요 (내용 확인 후 업데이트 예정).

### 3.2 `README.md` 현행화 필요
- `utils`와 `api` 디렉토리에 대한 설명이 누락되어 있음. 프로젝트 구조 섹션에 추가하여 신규 개발자의 혼란을 방지할 필요 있음.

### 3.3 테스트 확장
- 통합 테스트(`integration`)가 상대적으로 적음. 전체 파이프라인 흐름을 검증하는 E2E 성격의 테스트 보강 고려.

## 4. 결론
프로젝트는 전반적으로 **Clean Architecture**와 **SOLID 원칙**을 잘 따르고 있으며, 구조화가 잘 되어 있음. 다만, `README.md`의 최신화와 일부 모호한 디렉토리(`api`)에 대한 정리가 필요함.
