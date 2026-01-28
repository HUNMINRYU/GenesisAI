# Video Duplicate Click Prevention Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 비디오 생성 버튼의 중복 클릭으로 인한 중복 실행을 방지한다.

**Architecture:** Streamlit UI에서 SessionManager 플래그를 읽어 버튼을 비활성화하고, 실행 시작 시 플래그를 True로 설정한 뒤 종료 시 False로 리셋한다. 세션 기본값과 리셋 경로에 플래그를 포함해 UI가 일관되게 동작하도록 한다.

**Tech Stack:** Python, Streamlit, pytest

---

### Task 1: SessionManager에 VIDEO_GENERATING 상태 추가

**Files:**
- Modify: `src/genesis_ai/presentation/state/session_manager.py`
- Create: `tests/unit/test_session_manager_video_generating.py`

**Step 1: Write the failing test**

```python
import streamlit as st

from genesis_ai.presentation.state.session_manager import SessionManager


def test_init_session_state_sets_video_generating_flag():
    st.session_state.clear()
    SessionManager.init_session_state()
    assert SessionManager.get(SessionManager.VIDEO_GENERATING) is False


def test_reset_pipeline_state_resets_video_generating_flag():
    st.session_state.clear()
    SessionManager.init_session_state()
    SessionManager.set(SessionManager.VIDEO_GENERATING, True)
    SessionManager.reset_pipeline_state()
    assert SessionManager.get(SessionManager.VIDEO_GENERATING) is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/test_session_manager_video_generating.py -v`
Expected: FAIL with `AttributeError: type object 'SessionManager' has no attribute 'VIDEO_GENERATING'` or missing default

**Step 3: Write minimal implementation**

- `SessionManager`에 `VIDEO_GENERATING = "video_generating"` 상수 추가
- `init_session_state()` 기본값에 `VIDEO_GENERATING: False` 추가
- `reset()` 및 `reset_pipeline_state()`에서 `VIDEO_GENERATING`를 `False`로 리셋

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/test_session_manager_video_generating.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/genesis_ai/presentation/state/session_manager.py tests/unit/test_session_manager_video_generating.py
git commit -m "feat: add video generating session flag"
```

---

### Task 2: 비디오 생성 버튼 중복 클릭 방지

**Files:**
- Modify: `src/genesis_ai/presentation/tabs/tab_video.py`

**Step 1: Write the failing test**

수동 UI 동작 확인이므로 자동 테스트 대신 수동 검증 절차를 정의한다.

**Step 2: Manual verification (pre-change)**

- UI에서 `🎬 이 프롬프트로 영상 생성` 또는 `🎬 비디오 생성` 버튼을 빠르게 2~3회 클릭
- 동일 요청이 중복 실행되는 현상을 확인

**Step 3: Write minimal implementation**

- `is_generating = SessionManager.get(SessionManager.VIDEO_GENERATING, False)` 추가
- `🎬 이 프롬프트로 영상 생성` 버튼에 `disabled=is_generating` 적용
- `🎬 비디오 생성` 버튼에 `disabled=is_generating` 적용
- 각 버튼 클릭 시 `SessionManager.set(SessionManager.VIDEO_GENERATING, True)` 수행
- 비디오 생성 로직을 `try/finally`로 감싸 `finally`에서 `SessionManager.set(SessionManager.VIDEO_GENERATING, False)` 수행

**Step 4: Manual verification (post-change)**

- 버튼 연속 클릭 시 두 번째 클릭이 비활성화되어 실행되지 않는지 확인
- 영상 생성 완료 후 버튼이 다시 활성화되는지 확인

**Step 5: Commit**

```bash
git add src/genesis_ai/presentation/tabs/tab_video.py
git commit -m "fix: prevent duplicate video generation clicks"
```
