# Veo 3.1 프롬프트 구조 분석 및 영향도 평가 (Triage Report)

## 1. 개요 (Overview)
본 문서는 Google Veo 3.1 모델을 활용한 비디오 생성 템플릿(Dual Phase / Single Phase)의 구조적 안정성을 진단하고, 해당 구조가 시스템 및 사용자 경험에 미치는 영향을 분석합니다. 특히 '거부(Refusal)' 회피와 '일관성(Consistency)' 유지에 초점을 맞춥니다.

## 2. 구조적 문제점 파악 (Problem Identification)

### A. Dual Phase 모드 (12초 연장 전략)의 리스크
1.  **연결성 불일치 (Consistency Drift)**
    - *문제*: Phase 1(0-8초)의 마지막 프레임을 Phase 2(8-12초)의 초기 이미지로 사용할 때, 조명(Lighting)이나 피사체(Subject)의 디테일이 미세하게 변형될 위험이 있습니다.
    - *원인*: VEO 모델이 프레임을 해석할 때 'Generic'한 프롬프트에서 'Specific'한 브랜드 요소로 전환되는 과정에서 시각적 충돌 발생 가능.
2.  **안전성 필터 오작동 (Safety Filter & Refusal)**
    - *문제*: Phase 1에서는 Nike, iPhone 등 구체적 상표를 배제(Generic)하였으나, Phase 2에서 갑자기 브랜드 요소가 등장할 경우 모델이 이를 '맥락 없는 상표 노출'로 오인하여 생성을 거부(Refusal)하거나 블러(Blur) 처리할 수 있습니다.
3.  **지연 시간 (Latency) 및 실패율**
    - *문제*: 직렬 프로세스(Phase 1 성공 → Phase 2 생성)로 인해 전체 성공률이 `P(Phase1) * P(Phase2)`로 낮아집니다. Phase 2 실패 시 사용자는 8초짜리 결과물만 얻거나, 전체 실패로 인식할 수 있습니다.

### B. Single Phase 모드 (8초 표준)의 한계
1.  **스토리텔링의 부족**
    - *문제*: 8초라는 시간은 '기승전결'을 모두 담기에 부족할 수 있으며, 특히 마지막에 브랜드를 각인시키는(Brand Stamp) 여유 시간이 부족합니다.
2.  **정보 밀도 과부하**
    - *문제*: 8초 안에 Setting, Action, Brand Reveal을 모두 넣으려다 보면 움직임이 급격해지거나(Whip Pan 등), 시각적 정보량이 많아져 영상 품질(Artifacts)이 저하될 수 있습니다.

## 3. 영향도 지도 (Impact Map)

| 구분       | 영향 요소               | 영향도 (High/Med/Low) | 상세 내용                                                                                                                        |
| :--------- | :---------------------- | :-------------------: | :------------------------------------------------------------------------------------------------------------------------------- |
| **UX**     | **대기 시간 (Latency)** |       **High**        | Dual Phase의 경우 2번의 생성 과정을 거치므로 사용자가 체감하는 대기 시간이 2배 이상 증가할 수 있음.                              |
| **UX**     | **결과물 만족도**       |      **Medium**       | Phase 1과 Phase 2의 질감 차이가 발생할 경우, 프리미엄 느낌을 저해함.                                                             |
| **Tech**   | **파이프라인 복잡도**   |       **High**        | 생성된 영상을 다시 Input Image로 넣는 재귀적 로직(Recursive Logic) 관리 필요. 실패 시 롤백(Rollback) 처리 로직 필요.             |
| **Tech**   | **토큰/비용 효율**      |      **Medium**       | Phase 2 생성을 위한 추가 API 호출 비용 및 연산 자원 소모.                                                                        |
| **Safety** | **정책 위반 (Policy)**  |       **High**        | 텍스트(Text) 생성을 엄격히 금지하는 Veo 정책상, Phase 2의 'On-screen Dialogue' 요청이 거부될 확률이 높음. (OCR 감지로 인한 차단) |

## 4. 완화 전략 및 제언 (Mitigation Strategies)

### A. 기술적 완화 (Technical)
1.  **Fallback 메커니즘 구축**:
    - Phase 2 생성 실패 시, 즉시 Phase 1(8초) 결과물을 최종 산출물로 제공하는 'Graceful Degradation' 로직 구현.
2.  **Safety Check Pre-flight**:
    - Phase 2 프롬프트 투입 전, 금칙어(NSFC, Violence 등) 외에 상표권 관련 키워드가 시각적 묘사(Visual Description)에 포함되지 않도록 검수하는 전처리 단계 강화.

### B. 프롬프트 엔지니어링 (Prompt Engineering)
1.  **Strict No-Text Rule**:
    - 템플릿 상 `On-screen Dialogue` 항목이 있으나, Veo 모델은 텍스트 생성에 취약하므로 이를 영상 내 텍스트가 아닌, **후처리(Post-production) 단계의 자막 오버레이**로 처리하도록 가이드 변경 필요.
2.  **Visual Bridge**:
    - Phase 1의 마지막 2초(6-8초)를 '정적인(Static)' 샷으로 유도하여 Phase 2의 'Freeze frame'과 자연스럽게 이어지도록 설계.

## 5. 결론 (Conclusion)
제안된 템플릿 구조는 스토리텔링 확장에 유리하나(Mode A), **연속성 유지**와 **Safety Refusal**이 가장 큰 병목이 될 것입니다. 따라서 초기 런칭 시에는 **Mode B(Single Phase)를 기본값**으로 하되, Mode A는 '실험적 기능(Beta)'으로 제공하거나, 브랜드 노출을 영상 생성이 아닌 **후반 작업(Editing) 단계**에서 처리하는 하이브리드 방식을 권장합니다.
