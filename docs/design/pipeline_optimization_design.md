# 파이프라인 최적화 설계 문서

**작성일:** 2026-01-27
**기반 문서:** `gemini/docs/analysis/pipeline_optimization_proposal.md`
**역할:** 설계 및 리팩터링 계획 (구현 제외)

---

## 1. 문제 재정의

### 1.1 비디오 생성 중복 실행 (심각)
- **현상:** Veo Video Generation이 2회 실행됨 (126초 + 61초)
- **원인:** UI 레벨에서 중복 클릭 방지 메커니즘 부재
- **영향:** 전체 파이프라인 시간의 56% 점유

### 1.2 순차 실행 병목
- **현상:** 썸네일 3장 순차 생성 (~75초), 데이터 수집 순차 실행
- **원인:** `for` 루프 순차 처리, 병렬화 미적용
- **영향:** 불필요한 대기 시간 발생

### 1.3 X-Algorithm 인사이트 0건
- **현상:** 댓글 수집 완료 후 분석 결과 0건
- **원인:** 필터링 로깅 부재로 원인 파악 불가
- **영향:** 마케팅 전략 품질 저하

---

## 2. 현재 구조 요약

### 2.1 파이프라인 실행 흐름
```
[데이터 수집] YouTube → Naver (순차)
      ↓
[X-Algorithm] 댓글 분석 → 인사이트 추출
      ↓
[마케팅 전략] 전략 생성
      ↓
[콘텐츠 생성] SNS → 썸네일 → 비디오 (순차)
      ↓
[업로드] GCS 업로드
```

### 2.2 병목 지점

| 단계 | 파일 | 라인 | 현재 방식 |
|------|------|------|----------|
| 데이터 수집 | `pipeline_service.py` | 99-119 | 순차 동기 |
| 썸네일 생성 | `thumbnail_service.py` | 429-449 | for 루프 순차 |
| 비디오 생성 | `tab_video.py` | 150, 388 | 중복 클릭 무방비 |
| 필터링 | `filter.py` | 15-36 | 로깅 없음 |

---

## 3. 해결안 제시

### 해결안 A: UI 레벨 중복 클릭 방지 (추천)

**대상 파일:** `src/genesis_ai/presentation/tabs/tab_video.py`

**접근 방식:**
1. `SessionManager`를 활용한 상태 플래그 관리
2. `st.button(disabled=...)` 속성으로 버튼 비활성화
3. `try/finally` 블록으로 안전한 상태 리셋

**수정 위치:**
- 라인 150: Vision-Narrative 모드 버튼
- 라인 388: 수동 모드 버튼

**구현 스케치:**
```python
# tab_video.py 수정
is_generating = SessionManager.get("VIDEO_GENERATING", False)

if st.button("영상 생성", type="primary", disabled=is_generating):
    SessionManager.set("VIDEO_GENERATING", True)
    try:
        with st.spinner("Veo가 영상을 생성하고 있습니다..."):
            video_result = services.video_service.generate_from_image(...)
    finally:
        SessionManager.set("VIDEO_GENERATING", False)
        st.rerun()
```

---

### 해결안 B: 데이터 수집 병렬화 (추천)

**대상 파일:** `src/genesis_ai/services/pipeline_service.py`

**참조 패턴:** `tab_ab_test.py:1` - `ThreadPoolExecutor` 이미 사용 중

**접근 방식:**
1. `ThreadPoolExecutor(max_workers=2)` 사용
2. YouTube + Naver 동시 수집
3. 에러 발생 시 부분 결과 사용

**수정 위치:** 라인 99-119 대체

**구현 스케치:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def _collect_data_parallel(self, product, config):
    """YouTube + Naver 병렬 수집"""
    results = {}
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = {
            executor.submit(
                self._youtube.collect_product_data,
                product=product,
                max_results=config.youtube_count,
                include_comments=config.include_comments,
            ): "youtube",
            executor.submit(
                self._naver.collect_product_data,
                product=product,
                max_results=config.naver_count,
            ): "naver",
        }
        for future in as_completed(futures):
            key = futures[future]
            try:
                results[key] = future.result()
            except Exception as e:
                log_error(f"{key} 수집 실패: {e}")
                results[key] = {}
    return results
```

---

### 해결안 C: 썸네일 병렬 생성 (추천)

**대상 파일:** `src/genesis_ai/services/thumbnail_service.py`

**수정 위치:** 라인 429-449 (`generate_multiple` 메서드)

**접근 방식:**
1. `ThreadPoolExecutor(max_workers=3)` 사용
2. 3장 동시 생성
3. 진행률 콜백 스레드 안전 처리

**구현 스케치:**
```python
import threading
from concurrent.futures import ThreadPoolExecutor

def generate_multiple(self, product, hook_texts, styles=None, progress_callback=None):
    """여러 스타일 썸네일 병렬 생성"""
    if styles is None:
        styles = ["dramatic"] * len(hook_texts)

    results = []
    total = len(hook_texts)
    completed = [0]  # 리스트로 래핑 (클로저용)
    lock = threading.Lock()

    def generate_one(idx, hook_text, style_key):
        image = self.generate(
            product=product,
            hook_text=hook_text,
            style=style_key,
            include_text_overlay=True,
        )
        with lock:
            completed[0] += 1
            if progress_callback:
                progress_callback(f"썸네일 {completed[0]}/{total}", int((completed[0]/total)*100))
        if image:
            return {"image": image, "hook_text": hook_text, "style": style_key}
        return None

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [
            executor.submit(generate_one, i, hook_texts[i], styles[i % len(styles)])
            for i in range(total)
        ]
        for future in futures:
            result = future.result()
            if result:
                results.append(result)

    if progress_callback:
        progress_callback("모든 썸네일 생성 완료!", 100)

    return results
```

---

### 해결안 D: 필터링 로깅 추가 (추천)

**대상 파일:** `src/genesis_ai/services/pipeline/stages/filter.py`

**수정 위치:** 전체 클래스 리팩터링

**접근 방식:**
1. 필터링 사유별 통계 수집
2. 로그 출력으로 디버깅 용이성 확보
3. `get_stats()` 메서드로 외부 노출

**구현 스케치:**
```python
from typing import List, Optional

from genesis_ai.services.pipeline.types import Candidate
from genesis_ai.utils.logger import log_info


class QualityFilter:
    """X-Algorithm의 Pre-Scoring Filtering 단계"""

    MIN_LENGTH = 5
    SPAM_KEYWORDS = ["광고", "홍보", "http", "카톡", "사다리", "토토"]

    def __init__(self):
        self.stats = {"too_short": 0, "spam": 0, "toxic": 0, "passed": 0}

    def filter(self, candidates: List[Candidate]) -> List[Candidate]:
        self._reset_stats()
        filtered_candidates = []

        for candidate in candidates:
            reason = self._check_eligibility(candidate)
            if reason is None:
                filtered_candidates.append(candidate)
                self.stats["passed"] += 1
            else:
                self.stats[reason] += 1

        log_info(f"QualityFilter 결과: 입력 {len(candidates)}건 → 통과 {self.stats['passed']}건")
        log_info(f"  - 길이 미달: {self.stats['too_short']}건")
        log_info(f"  - 스팸 키워드: {self.stats['spam']}건")
        log_info(f"  - 독성 초과: {self.stats['toxic']}건")

        return filtered_candidates

    def _check_eligibility(self, candidate: Candidate) -> Optional[str]:
        # 1. 길이 필터
        if len(candidate.content.strip()) < self.MIN_LENGTH:
            return "too_short"

        # 2. 스팸 키워드 필터
        for keyword in self.SPAM_KEYWORDS:
            if keyword in candidate.content:
                return "spam"

        # 3. Toxicity 필터
        if candidate.features.toxicity > 0.8:
            return "toxic"

        return None

    def _reset_stats(self):
        self.stats = {"too_short": 0, "spam": 0, "toxic": 0, "passed": 0}

    def get_stats(self) -> dict:
        return self.stats.copy()
```

---

## 4. 추천안 선택

| 문제 | 추천안 | 이유 |
|------|--------|------|
| 비디오 중복 실행 | 해결안 A | 최소 변경, 즉각 효과, 비용 절감 |
| 데이터 수집 병목 | 해결안 B | 기존 패턴 준수, 메서드 시그니처 유지 |
| 썸네일 생성 병목 | 해결안 C | 66% 시간 단축, 독립 작업 병렬화 |
| X-Algorithm 0건 | 해결안 D | 진단 우선, 데이터 기반 조정 가능 |

---

## 5. 변경 범위

### 수정 대상 파일

| 파일 경로 | 변경 내용 | 우선순위 |
|-----------|----------|---------|
| `src/genesis_ai/presentation/tabs/tab_video.py` | 버튼 disabled 상태 관리 | P0 |
| `src/genesis_ai/services/pipeline_service.py` | 데이터 수집 병렬화 | P1 |
| `src/genesis_ai/services/thumbnail_service.py` | 썸네일 병렬 생성 | P1 |
| `src/genesis_ai/services/pipeline/stages/filter.py` | 필터링 통계 로깅 | P1 |
| `src/genesis_ai/services/pipeline/orchestrator.py` | stats에 filter_details 포함 | P2 |

### 수정하지 않는 파일

| 파일 경로 | 이유 |
|-----------|------|
| `veo_client.py` | UI에서 중복 방지가 우선 |
| `comment_analysis_service.py` | 필터링 원인 파악 후 조정 |
| `youtube_service.py` | 호출 레이어에서 병렬화 |
| `naver_service.py` | 호출 레이어에서 병렬화 |
| `video_service.py` | 서비스 로직 안정 |
| `hydration.py` | 이미 asyncio.gather 적용됨 |

---

## 6. 리스크

| 리스크 | 영향도 | 발생 확률 | 완화 전략 |
|--------|--------|-----------|-----------|
| ThreadPoolExecutor 스레드 경합 | 중 | 낮음 | max_workers 제한 (2~3) |
| Streamlit rerun 충돌 | 중 | 중간 | 상태 플래그로 완료 대기 |
| 진행률 콜백 스레드 안전 | 낮음 | 중간 | threading.Lock 사용 |
| 필터링 완화 시 노이즈 증가 | 낮음 | 중간 | 통계 기반 점진적 조정 |

---

## 7. 구현용 체크리스트

### Phase 1: 비디오 중복 클릭 방지 (P0)
- [ ] `tab_video.py:150` Vision-Narrative 버튼에 disabled 적용
- [ ] `tab_video.py:388` 수동 모드 버튼에 disabled 적용
- [ ] `SessionManager`에 `VIDEO_GENERATING` 상태 플래그 추가
- [ ] try/finally로 예외 발생 시에도 플래그 리셋 보장
- [ ] 테스트: 연속 클릭 시 1회만 실행 확인

### Phase 2: 필터링 로깅 추가 (P1)
- [ ] `filter.py`에 stats 딕셔너리 추가
- [ ] `_check_eligibility()` 메서드로 사유별 분류
- [ ] `get_stats()` 메서드 추가
- [ ] `log_info()`로 필터링 결과 출력
- [ ] 테스트: X-Algorithm 실행 후 로그 확인

### Phase 3: 썸네일 병렬 생성 (P1)
- [ ] `thumbnail_service.py`에 `ThreadPoolExecutor` import 추가
- [ ] `generate_multiple()` 메서드 병렬화
- [ ] `threading.Lock`으로 진행률 콜백 보호
- [ ] 테스트: 생성 시간 75초 → 30초 이내 확인

### Phase 4: 데이터 수집 병렬화 (P1)
- [ ] `pipeline_service.py`에 `ThreadPoolExecutor` import 추가
- [ ] `_collect_data_parallel()` 헬퍼 메서드 추가
- [ ] `execute()` 메서드에서 기존 순차 호출 대체
- [ ] 에러 핸들링: 부분 실패 시 나머지 결과 사용
- [ ] 테스트: 수집 시간 50% 단축 확인

### Phase 5: stats 전파 (P2)
- [ ] `orchestrator.py`에서 `filter.get_stats()` 호출
- [ ] stats 딕셔너리에 `filter_details` 키 추가
- [ ] UI에서 0건일 때 원인 표시 (선택적)

---

## 8. 검증 방법

1. **중복 클릭 방지:**
   - 비디오 생성 버튼을 빠르게 3회 클릭
   - API 호출이 1회만 발생하는지 확인

2. **병렬화 성능:**
   - 썸네일 3장 생성 시간 측정 (목표: 30초 이내)
   - 데이터 수집 시간 측정 (목표: 기존 대비 50% 단축)

3. **필터링 로깅:**
   - X-Algorithm 실행 후 로그 확인
   - 0건일 때 원인(too_short, spam, toxic) 파악 가능 여부

---

**문서 끝**
