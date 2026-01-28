# `too many file descriptors in select()` 에러 분석

## 1. 문제 요약
- **발생 시점**: 비디오 생성 파이프라인 중 **X-Algorithm (Feature Hydration)** 단계 실행 시
- **에러 메시지**: `ValueError: too many file descriptors in select()`
- **현상**: 파이프라인 실행이 중단되며 분석이 실패함.

## 2. 관련 컴포넌트 및 파일
- **Orchestrator**: `src/genesis_ai/services/pipeline/orchestrator.py`
- **Component**: `src/genesis_ai/services/pipeline/stages/hydration.py` (`FeatureHydrator`)
- **Library**: Python `asyncio` (Windows Default Event Loop)

## 3. 원인 분석
이 에러는 **Windows 환경**의 `SelectorEventLoop`가 가진 **파일 디스크립터(소켓) 제한(512개)**을 초과하여 발생합니다.

분석 결과, `FeatureHydrator.hydrate` 메서드에서 동시성 제어가 누락되어 있습니다:

```python
# src/genesis_ai/services/pipeline/stages/hydration.py

async def hydrate(self, candidates: List[Candidate]) -> List[Candidate]:
    # ...
    # 모든 후보군(Candidate)에 대해 동시에 작업을 생성
    tasks = [self._analyze_single_comment(c) for c in candidates]
    
    # 제한 없이 모든 작업을 동시에 실행 (Gather)
    results = await asyncio.gather(*tasks) 
    return results
```

위 코드에서 `candidates`의 개수가 수백 개(예: 800개의 댓글)일 경우, `asyncio.gather`는 **800개의 Gemini API 연결을 동시에 시작**하려 시도합니다. 이는 Windows의 `select()` 시스템 콜 한계인 512개를 즉시 초과하여 크래시를 유발합니다.

## 4. 해결 방향 (제안)
코드를 직접 수정하는 대신, 다음 전략을 권장합니다:

1.  **동시성 제한 (Semaphore) 도입**
    - `FeatureHydrator` 클래스 내에 `asyncio.Semaphore(20)` 등을 선언하여, 동시에 실행되는 API 요청 수를 20~50개 수준으로 제한합니다.
    - `_analyze_single_comment` 내부 또는 호출 부에서 세마포어를 획득(`async with self.semaphore:`)하도록 변경합니다.

2.  **배치 처리 (Batching)**
    - 데이터를 `chunk` 단위로 나누어 순차적으로 처리하는 방식을 고려할 수 있습니다.

> **참고**: Windows가 아닌 환경(Linux/macOS)이나 `ProactorEventLoop`를 사용하는 경우 이 제한이 훨씬 높지만, 애플리케이션 레벨의 안정성을 위해 **Semaphore**를 사용하는 것이 가장 근본적인 해결책입니다.
