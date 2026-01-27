# HistoryService 저장 및 삭제 에러 분석 보고서

## 1. 개요 및 정의
**HistoryServiceSaveError** (주로 `PermissionError: [WinError 32]`)는 Windows 환경에서 `HistoryService`가 파이프라인 실행 결과(Metadata)를 저장하거나 테스트 종료 후 임시 디렉토리를 정리할 때 발생하는 파일 접근 권한 오류입니다.

이 문제는 파일이 생성된 직후 백신 프로그램, Windows Search Indexer, 또는 Python 프로세스 내부의 가비지 컬렉션 지연으로 인해 **파일이 잠겨 있는(Locked) 상태**에서 삭제나 덮어쓰기를 시도할 때 발생합니다.

## 2. 코드 레벨 발생 경로 (Call Stack)

에러는 주로 테스트 코드의 정리(Teardown) 단계나 명시적인 삭제 요청 시 발생합니다:

```mermaid
graph TD
    A[pytest teardown] -->|yield 종료| B[shutil.rmtree]
    B -->|파일 순회| C[os.unlink / os.remove]
    C -->|Windows File System| D{File Locked?}
    D -- Yes --> E[PermissionError: [WinError 32]]
    E -- 프로세스가 파일을 사용 중 --> F[Crash / Test Failure]
```

### 주요 파일 및 함수

1.  **`tests/unit/test_history_service.py`**:
    *   **Fixture**: `temp_base_dir`
    *   **로직**: `shutil.rmtree(temp_dir, ignore_errors=True)`를 호출하지만, 시점에 따라 실패 가능.
    *   **증상**: `pytest` 실행 시 간헐적 실패.

2.  **`src/genesis_ai/services/history_service.py`**:
    *   **메서드**: `delete_history(history_id)`
    *   **코드**: `file_path.unlink()`
    *   **이슈**: 파일 핸들이 확실히 닫혔음에도 OS 레벨에서 즉시 해제되지 않아 삭제 실패.

3.  **`src/genesis_ai/utils/file_store.py`**:
    *   **메서드**: `save_metadata`
    *   **코드**: `path.write_text(...)`
    *   **특이사항**: 파일 쓰기 자체는 원자적(Atomic)으로 처리되나, 직후에 다시 읽거나 삭제하려 할 때 문제가 됨.

## 3. 에러 재현 (Reproduction Steps)

### 시나리오 1: 단위 테스트 반복 실행
1.  Windows 환경에서 터미널을 연다.
2.  `pytest tests/unit/test_history_service.py -n 4` (xdist 병렬 실행) 또는 반복 실행 명령을 입력한다.
3.  **결과**: `PermissionError: [WinError 32] 다른 프로세스가 파일을 사용 중이기 때문에 프로세스가 액세스 할 수 없습니다.` 발생.

### 시나리오 2: 빠른 생성 및 삭제
1.  `HistoryService.save_result()`로 파일 생성.
2.  지연 없이 바로 `HistoryService.delete_history()` 호출.
3.  **결과**: 파일 시스템 속도나 백신 검사 타이밍에 따라 삭제 실패.

## 4. 해결 방안 (Mitigation)

### 단기 조치 (Retry Logic)
*   파일 삭제 로직에 **재시도 메커니즘(Retry)**을 추가합니다.
*   `tenacity` 라이브러리 등을 사용하여 `PermissionError` 발생 시 0.1초 대기 후 재시도하도록 수정합니다.

### 장기 개선 (Robust File Handling)
1.  **Atomic Write**: 임시 파일에 먼저 쓴 후 `os.replace`로 이동시키는 방식 사용 (Windows에서도 비교적 안전).
2.  **Temp Directory 관리**: `pytest`의 기본 `tmp_path` 픽스처를 사용하여 관리를 위임하거나, `shutil.rmtree` 호출 시 `onerror` 핸들러를 등록하여 권한 오류를 강제로 우회(`os.chmod` 등)하게 수정.
