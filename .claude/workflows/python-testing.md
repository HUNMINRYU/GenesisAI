---
description: Python 테스팅 패턴 및 가이드
---

# Python 테스팅 표준 (Testing Standards)

**목표**: `pytest`를 사용한 신뢰할 수 있고, 빠르며, 가독성 높은 테스트 작성.

## 1. 디렉토리 구조
```
tests/
├── conftest.py         # 공유 픽스쳐 (Shared fixtures)
├── test_app.py         # 통합 테스트 (Integration tests)
└── unit/               # 단위 테스트 (Unit tests)
    └── test_utils.py
```

## 2. 모범 사례 (Best Practices)

### 픽스쳐 (`conftest.py`)
`setup/teardown`을 위해 픽스쳐를 사용하십시오.
```python
@pytest.fixture
def mock_client():
    with patch('app.api.client') as mock:
        yield mock
```

### 파라미터화 (Parameterization)
반복문을 사용한 테스트 대신 `@pytest.mark.parametrize`를 사용하십시오.
```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6)
])
def test_double(input, expected):
    assert double(input) == expected
```

### 모의 객체 (Mocking - 외부 서비스)
 단위 테스트에서는 **절대로** 실제 API (GCP, YouTube, Gemini)를 호출하지 마십시오.
- `unittest.mock.patch` 또는 `pytest-mock`을 사용하십시오.
- 테스트가 오프라인에서도 실행되도록 보장하십시오.

## 3. 테스트 실행
- **전체 실행**: `pytest`
- **빠른 실행**: `pytest -m "not slow"` (마커 필요)
- **커버리지**: `pytest --cov=app`
