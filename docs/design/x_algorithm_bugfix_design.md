# X-Algorithm 데이터 파이프라인 버그 수정 설계 문서

**작성일:** 2026-01-27
**기반 문서:** `gemini/docs/analysis/x_algorithm_integration_strategy.md`
**역할:** 설계 및 리팩터링 계획 (구현 제외)

---

## 1. 문제 재정의

### 1.1 현상
- X-Algorithm 인사이트 분석 결과: **0건**
- 로그: `X-Algorithm 분석 완료: 0개 인사이트 도출`

### 1.2 원인
- `YoutubeClient.collect_video_data()` 메서드에서 `comments` 필드 누락
- `comments_count`(숫자)만 저장하고 실제 댓글 리스트 미포함

### 1.3 영향
- 마케팅 전략 생성 시 댓글 기반 인사이트 활용 불가
- X-Algorithm 파이프라인 전체 무력화

---

## 2. 현재 구조 요약

### 2.1 데이터 흐름 (버그 상태)

```
YoutubeClient.collect_video_data()
│
├─ comments = self.get_video_comments(v["id"])  # 댓글 수집 ✓
│
├─ collected_videos.append({
│      "comments_count": len(comments),  # 숫자만 저장 ✓
│      # "comments": comments  ← 이 줄 없음 ✗
│  })
│
└─ return {"videos": collected_videos, ...}
      │
      ↓
PipelineService.execute()
│
├─ for v in youtube_data["videos"]:
│      for c in v.get("comments", []):  # 항상 [] 반환 ✗
│          comments.append(...)
│
└─ self._orchestrator.run_pipeline(comments)  # 빈 리스트 전달
      │
      ↓
X-Algorithm: 입력 0건 → 인사이트 0건
```

### 2.2 버그 위치

| 파일 | 라인 | 문제 |
|------|------|------|
| `youtube_client.py` | 173-191 | `comments` 필드 누락 |
| `pipeline_service.py` | 128 | `v.get("comments", [])` 항상 빈 리스트 |

---

## 3. 해결안 제시

### 해결안 A: `comments` 필드 추가 (추천)

**대상 파일:** `src/genesis_ai/infrastructure/clients/youtube_client.py`

**수정 위치:** 라인 173-191 (`collect_video_data` 메서드)

**접근 방식:**
1. 기존 `collected_videos.append()` 딕셔너리에 `"comments": comments` 1줄 추가
2. 기존 로직 변경 없음
3. 메모리 영향 미미 (이미 `comments` 변수에 데이터 존재)

**구현 스케치:**

```python
# youtube_client.py 라인 173-191
# 수정 전
collected_videos.append({
    "keyword": keyword,
    "video_id": v["id"],
    "title": v["title"],
    "description": v["description"],
    "transcript": transcript[:2000] if transcript else v["description"][:500],
    "thumbnail": v.get("thumbnail", ""),
    "channel": v.get("channel", ""),
    "comments_count": len(comments),
})

# 수정 후
collected_videos.append({
    "keyword": keyword,
    "video_id": v["id"],
    "title": v["title"],
    "description": v["description"],
    "transcript": transcript[:2000] if transcript else v["description"][:500],
    "thumbnail": v.get("thumbnail", ""),
    "channel": v.get("channel", ""),
    "comments_count": len(comments),
    "comments": comments,  # ← 1줄 추가
})
```

---

## 4. 추천안 선택

| 항목 | 내용 |
|------|------|
| 추천안 | 해결안 A (`comments` 필드 추가) |
| 이유 | 최소 변경 (1줄), 기존 로직 유지, 즉각 효과 |

---

## 5. 변경 범위

### 수정 대상 파일

| 파일 경로 | 변경 내용 | 라인 | 우선순위 |
|-----------|----------|------|---------|
| `src/genesis_ai/infrastructure/clients/youtube_client.py` | `"comments": comments` 추가 | 189 | **P0 긴급** |

### 수정하지 않는 파일

| 파일 경로 | 이유 |
|-----------|------|
| `pipeline_service.py` | 이미 `v.get("comments", [])` 패턴 사용 중, 변경 불필요 |
| `orchestrator.py` | 입력만 정상화되면 정상 동작 |
| `filter.py` | 이전 작업에서 로깅 추가 완료 |
| `comment_analysis_service.py` | 변경 불필요 |
| `youtube_service.py` | 내부 클라이언트만 수정 |

---

## 6. 리스크

| 리스크 | 영향도 | 발생 확률 | 완화 전략 |
|--------|--------|-----------|-----------|
| 응답 데이터 크기 증가 | 낮음 | 중간 | 이미 수집된 데이터, 추가 API 호출 없음 |
| `top_comments`와 중복 | 낮음 | 높음 | 기능상 무해, 명확한 용도 구분 |

---

## 7. 구현용 체크리스트

### Phase 1: 긴급 버그 수정 (P0)

- [ ] `youtube_client.py` 파일 열기
- [ ] 라인 173-191 위치 확인 (`collected_videos.append`)
- [ ] `"comments_count": len(comments),` 다음 줄에 `"comments": comments,` 추가
- [ ] 파일 저장

### Phase 2: 검증

- [ ] 파이프라인 실행
- [ ] 로그 확인: `QualityFilter 결과: 입력 N건 → 통과 M건`
- [ ] 로그 확인: `X-Algorithm 분석 완료: N개 인사이트 도출`
- [ ] N > 0 확인

---

## 8. 검증 방법

1. **데이터 흐름 검증:**
   - 파이프라인 실행 후 `X-Algorithm 분석 완료` 로그 확인
   - 인사이트 개수 > 0 확인

2. **QualityFilter 로그 검증:**
   - `QualityFilter 결과: 입력 N건` 에서 N > 0 확인
   - 이전에 추가한 필터링 통계 로깅으로 데이터 흐름 추적

3. **UI 검증:**
   - 마케팅 전략 생성 시 인사이트 기반 추천 동작 확인

---

## 9. 향후 고도화 방향 (참고)

Gemini 분석 문서에서 제안한 X-Algorithm 아키텍처:

| 단계 | 현재 상태 | 고도화 방향 |
|------|----------|------------|
| Candidate Generation | 단순 수집 | In/Out-Network 분류 |
| Light Ranker | QualityFilter (기본) | 한글 비율 필터 추가 |
| Heavy Ranker | 미구현 | 스코어링 모델 도입 |
| SimClusters | 미구현 | 유사 댓글 클러스터링 |

**참고:** 고도화는 Phase 1 완료 후 별도 설계 문서로 진행

---

**문서 끝**
