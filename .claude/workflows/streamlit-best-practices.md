---
description: Streamlit Best Practices & Testing Guide
---

# Streamlit 개발 워크플로우

**목표**: 확장 가능하고, 테스트 가능하며, 성능이 뛰어난 Streamlit 앱을 구축합니다.

## 1. 프로젝트 구조
확장성을 위해 멀티페이지 앱 구조 또는 탭 구조를 사용합니다:

```
app/
├── app.py              # 진입점 (Entry point)
├── pages/              # (옵션 A) 멀티페이지 앱
│   ├── 1_dashboard.py
│   └── 2_settings.py
├── tabs/               # (옵션 B) 탭 기반 단일 페이지 앱
│   └── tab_home.py
├── components/         # 재사용 가능한 UI 위젯
└── styles.py           # 중앙 집중식 CSS/스타일링
```

## 2. 상태 및 캐싱 (State & Caching)
- **세션 상태 (Session State)**: `app.py` 상단에서 모든 키를 초기화합니다.
  ```python
  if 'user_data' not in st.session_state:
      st.session_state.user_data = {}
  ```
- **캐싱 (Caching)**: 데이터는 `@st.cache_data`, DB 연결/ML 모델은 `@st.cache_resource`를 사용합니다.

## 3. 자동화 테스트 (브라우저 불필요)
빠른 헤드리스 테스트를 위해 `AppTest`를 사용합니다.

**예시 `tests/test_app_flow.py`**:
```python
from streamlit.testing.v1 import AppTest

def test_app_loads():
    at = AppTest.from_file("app/app.py")
    at.run()
    assert not at.exception

def test_interaction():
    at = AppTest.from_file("app/app.py")
    at.run()
    at.button[0].click().run()
    assert "Success" in at.markdown[0].value
```

## 4. UI/UX 규칙
- **피드백**: 긴 작업 시 항상 `st.spinner()` 또는 `st.status()`를 표시합니다.
- **레이아웃**: `st.columns`와 `st.expander`를 사용하여 혼잡함을 줄입니다.
- **테마**: `.streamlit/config.toml`에 브랜드에 맞는 색상을 정의합니다.
