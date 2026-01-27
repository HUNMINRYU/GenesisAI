# Veo 3.1 프롬프트 구조 개선 계획

## 요약
Veo 3.1 비디오 생성의 Dual Phase/Single Phase 구조 문제를 해결하기 위한 2단계 전략 제시

---

## 1. 현재 문제점

### Dual Phase (12초) 리스크
- **연결성 불일치**: Phase 1→2 전환 시 조명/피사체 변형
- **Safety Filter 오작동**: 브랜드 요소 갑작스런 등장 시 거부
- **지연 시간**: 직렬 프로세스로 전체 성공률 저하

### Single Phase (8초) 한계
- 스토리텔링 시간 부족
- 정보 밀도 과부하

---

## 2. 해결 전략

### Strategy A: 최소 변경 (권장 - 1차 PR)
핵심 버그 수정에만 집중, 빠른 배포 가능

### Strategy B: 구조 개선 (2차 PR)
유지보수성 향상을 위한 리팩토링

---

## 3. PR 분리 계획

### PR #1: 핵심 버그 수정 (Strategy A)
**범위**: Safety 체크, Phase 2 폴백
**예상 변경**: ~150줄
**위험도**: 낮음

### PR #2: 구조 개선 (Strategy B)
**범위**: Phase Executor 분리, SafetyValidator 클래스
**예상 변경**: ~400줄
**위험도**: 중간

---

## 4. 수정 체크리스트

### PR #1 체크리스트 (최소 변경)
- [ ] `veo_template.py` - Safety 체크리스트 추가
- [ ] `veo_client.py` - `_pre_flight_safety_check()` 구현
- [ ] `veo_client.py` - `generate_video_with_fallback()` 구현
- [ ] `video_service.py` - `_validate_prompt_safety()` 추가
- [ ] `video_service.py` - generate() 함수에 safety 호출 추가
- [ ] `test_video_service.py` - 새 테스트 케이스 추가
- [ ] 3개 병렬 구현 (claude/, codex/, gemini/) 동기화

### PR #2 체크리스트 (구조 개선)
- [ ] `core/validators/safety_validator.py` 생성
- [ ] `infrastructure/clients/phase_executor.py` 생성
- [ ] `veo_client.py` 리팩토링 (Phase Executor 주입)
- [ ] `video_service.py`에 VideoGenerationMode enum 추가
- [ ] `video_generator.py` 인터페이스 확장
- [ ] 통합 테스트 추가
- [ ] 3개 병렬 구현 동기화

---

## 5. 변경할 함수/모듈 경계

### 수정 대상 파일

| 파일 | 수정 내용 | PR |
|------|----------|-----|
| `infrastructure/clients/veo_client.py` | Safety 체크, 폴백 로직 | #1, #2 |
| `services/video_service.py` | 모드 선택, 검증 로직 | #1, #2 |
| `core/prompts/veo_template.py` | Safety 가이드라인 | #1 |
| `core/exceptions.py` | 새 에러 타입 (필요시) | #2 |
| `tests/unit/test_video_service.py` | 테스트 케이스 | #1, #2 |

### 신규 생성 파일 (PR #2)

| 파일 | 책임 |
|------|------|
| `core/validators/safety_validator.py` | Veo 프롬프트 Safety 검증 |
| `infrastructure/clients/phase_executor.py` | Phase 1/2 실행 로직 분리 |
| `tests/unit/test_safety_validator.py` | Safety 테스트 |
| `tests/unit/test_phase_executor.py` | Phase 실행 테스트 |

---

## 6. 테스트 보강 포인트

### PR #1 테스트 추가
```python
def test_pre_flight_safety_blocks_nsfw_content():
    """NSFW 프롬프트 차단 검증"""

def test_fallback_to_phase1_on_phase2_failure():
    """Phase 2 실패 시 Phase 1 결과 반환 검증"""

def test_single_phase_is_default():
    """Single Phase가 기본값인지 확인"""

def test_dual_phase_requires_beta_flag():
    """Dual Phase는 beta 플래그 필요"""
```

### PR #2 테스트 추가
```python
# test_safety_validator.py
def test_blocks_real_person_names(): ...
def test_blocks_trademark_logos(): ...
def test_allows_generic_descriptions(): ...

# test_phase_executor.py
def test_phase1_generates_8_second_video(): ...
def test_phase2_requires_phase1_frame(): ...
def test_phase2_fallback_returns_phase1_on_failure(): ...
```

---

## 7. 검증 방법

### 단위 테스트
```bash
cd claude && pytest tests/unit/test_video_service.py -v
cd codex && pytest tests/unit/test_video_service.py -v
cd gemini && pytest tests/unit/test_video_service.py -v
```

### E2E 수동 테스트
1. Streamlit UI 실행
2. Single Phase 모드로 비디오 생성 → 8초 영상 확인
3. Dual Phase (Beta) 모드로 생성 → 12초 또는 8초 폴백 확인
4. Safety 차단 테스트 → 금칙어 포함 프롬프트 거부 확인

---

## 8. 위험 평가

| 위험 요소 | 수준 | 완화 방안 |
|----------|------|----------|
| 기존 API 호환성 | 낮음 | 기존 시그니처 유지, 새 파라미터는 optional |
| Safety 오탐지 | 중간 | 로깅 강화, bypass 옵션 제공 |
| Phase 2 폴백 혼란 | 낮음 | UI에 "8초 버전 생성됨" 알림 |
| 3개 구현 동기화 | 높음 | 공통 모듈 추출 검토 |

---

## 9. 핵심 파일 경로

```
genesis-ai-wt/claude/src/genesis_ai/
├── infrastructure/clients/veo_client.py      # 773 lines
├── services/video_service.py                 # 263 lines
├── core/prompts/veo_template.py              # 82 lines
├── core/prompts/veo_prompt_engine.py         # 137 lines
├── core/exceptions.py                        # 340 lines
└── tests/unit/test_video_service.py          # 74 lines
```

동일 구조가 `codex/`, `gemini/` 폴더에 존재

---

## 10. 권장 구현 순서

1. **즉시 배포 (PR #1)**: Safety 체크 + 폴백 로직으로 현재 문제 해결
2. **후속 배포 (PR #2)**: 구조적 개선으로 장기 유지보수성 확보
3. **Single Phase를 기본값으로 설정**, Dual Phase는 Beta 플래그로 관리
