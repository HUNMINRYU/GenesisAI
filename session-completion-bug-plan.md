# SessionManager 파이프라인 완료 플래그 버그 분석 보고서

## 1. 개요 및 정의
**Session Completion Bug**는 파이프라인 실행 중 치명적인 오류(Critical Exception)가 발생하거나 실행이 완료된 직후, `SessionManager.PIPELINE_EXECUTED` 상태 플래그가 올바르게 갱신되지 않거나 UI 상태와 동기화되지 않는 현상을 말합니다.

이로 인해 사용자는 다음과 같은 경험을 할 수 있습니다:
1.  **로그 소실**: 실행 중 에러가 발생했으나, 다른 탭을 다녀오면 에러 로그와 상태가 사라짐.
2.  **무한 대기 오해**: 실행 완료 후 UI가 즉시 리프레시되지 않아(버튼 클릭 스코프 내 잔존), 사용자가 여전히 '실행 중'으로 오해.

## 2. 코드 레벨 발생 경로 (Call Stack)

### 시나리오 1: Critical Exception 발생 시 상태 미갱신

```mermaid
graph TD
    A[tab_pipeline._execute_pipeline] -->|Start| B[SessionManager.reset_pipeline_state]
    B -->|PIPELINE_EXECUTED = False| C[Try Block]
    C -->|Error before execute| D[Exception Block]
    D -->|Log Error| E[st.error]
    E -->|Finish| F[End of Function]
    F -- No set_pipeline_result --> G[State remains False]
```

*   **`src/genesis_ai/presentation/tabs/tab_pipeline.py`**:
    *   `_execute_pipeline` 함수 내 `try...except` 블록에서 예외 발생 시(Line 201), 에러 로그만 남기고 `SessionManager.set_pipeline_result()`를 호출하지 않음.
    *   결과적으로 `PIPELINE_EXECUTED`가 `False`로 남음.
    *   `st.button` 스코프가 끝나면(다른 인터랙션 시) 로그와 에러 메시지가 화면에서 사라짐.

### 시나리오 2: 성공 후 UI 리프레시 부재

*   파이프라인 성공 시(Line 146) `render_pipeline_results`를 호출하여 **현재 프레임**에 결과를 그림.
*   하지만 `st.rerun()`을 호출하지 않아, 사용자는 여전히 "버튼이 눌린 상태(Button Action Scope)" 안에 머묾.
*   이 상태에서는 다른 위젯 조작 시 예측 불가능한 UI 리셋이 발생할 수 있음.

## 3. 에러 재현 (Reproduction Steps)

### 재현 1: 초기화단계 강제 에러
1.  `_execute_pipeline`의 `get_services()` 호출 직전 `raise ValueError("Simulated Crash")` 코드 삽입.
2.  "파이프라인 실행" 버튼 클릭.
3.  화면에 "치명적 오류" 표시됨.
4.  사이드바에서 다른 탭으로 이동했다가 다시 복귀.
5.  **결과**: 실행했던 오류 로그와 메시지가 모두 사라지고 초기 상태로 리셋됨 (`PIPELINE_EXECUTED`가 False라서).

## 4. 해결 방안 (Mitigation)

### 단기 조치 (Finally Block)
*   `_execute_pipeline`의 `try...except` 구문에 `finally` 블록을 추가하지 말고, **`except` 블록 내에서도 상태를 갱신**하도록 수정.
*   실패 상태(`PipelineResult(success=False, ...)`)를 생성하여 `set_pipeline_result`를 호출, 최소한 "실패했음"을 세션에 남겨야 함.

### 장기 개선 (Explicit Rerun)
1.  **Force Rerun**: 실행 완료(성공/실패) 후 `st.rerun()`을 호출하여 버튼 스코프를 탈출하고, `elif SessionManager.get(PIPELINE_EXECUTED):` 블록에서 결과가 렌더링되도록 흐름 변경.
2.  **Persistent Logs**: 파이프라인 로그를 `PipelineResult` 객체나 별도 세션 키에 영구 보관하여 리프레시 후에도 유지.

---

## 해결 전략: 2개 PR 분리

### PR #1: 기능 수정 (except 블록 상태 갱신)
**목적**: 예외 발생 시에도 `PIPELINE_EXECUTED` 플래그 설정

### PR #2: UX 개선 (st.rerun 호출)
**목적**: 실행 완료 후 버튼 스코프 탈출로 안정적인 UI 상태

---

## PR #1 상세 계획

### 체크리스트

- [ ] `_execute_pipeline` except 블록에서 실패 `PipelineResult` 생성
- [ ] `SessionManager.set_pipeline_result(failed_result)` 호출
- [ ] 에러 메시지를 `PipelineResult.error_message`에 저장

### 변경 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/genesis_ai/presentation/tabs/tab_pipeline.py` | except 블록에서 상태 갱신 |

### 코드 변경 예시

```python
# tab_pipeline.py - _execute_pipeline
except Exception as e:
    logger.error(f"파이프라인 치명적 오류: {e}")
    st.error(f"치명적 오류 발생: {e}")

    # 실패 상태 저장 (추가)
    failed_result = PipelineResult(
        success=False,
        product_name=product.get("name", "Unknown"),
        config=config,
        error_message=str(e),
    )
    SessionManager.set_pipeline_result(failed_result)
```

---

## PR #2 상세 계획

### 체크리스트

- [ ] 성공/실패 후 `st.rerun()` 호출 추가
- [ ] 결과 렌더링을 `PIPELINE_EXECUTED` 조건 블록으로 이동

### 코드 변경 예시

```python
# 성공 시
SessionManager.set_pipeline_result(result)
st.rerun()  # 버튼 스코프 탈출

# 실패 시
SessionManager.set_pipeline_result(failed_result)
st.rerun()  # 버튼 스코프 탈출
```

---

## 테스트 보강 포인트

| 테스트 케이스 | 설명 |
|--------------|------|
| 예외 발생 시 `PIPELINE_EXECUTED` 플래그 확인 | except 블록 동작 검증 |
| 실패 결과의 `error_message` 포함 확인 | 에러 정보 보존 검증 |
| 탭 이동 후 결과 유지 확인 | 상태 영속성 검증 |

---

## 우선순위 권장

1. **PR #1 먼저** - 로그 소실 문제 해결 (심각도 높음)
2. **PR #2 이후** - UX 안정성 개선

## 예상 변경 규모

| PR | 파일 수 | LOC 변경 |
|----|--------|----------|
| #1 | 1 | ~15 |
| #2 | 1 | ~10 |
