---
description: .agent/skills에 쌓인 암묵지를 실행 가능한 workflow 문서로 전환한다. 지식을 재사용 가능한 자산으로 만든다.
---

- Trigger
  - skills 문서가 누적되기 시작했을 때

- Goal
  - skill을 workflow로 승격한다

- Inputs
  - skills_index.json
  - 주요 SKILL.md 문서

- Steps
  1. 기존 workflow 문서 구조를 분석한다
  2. 재사용 가치가 높은 skill을 선별한다
  3. 다음 구조로 변환한다
     - Trigger
     - Inputs
     - Steps
     - Failure Handling
     - Validation
  4. 모든 workflow를 실제로 실행해본다

- Validation
  - workflow만 보고 동일 작업을 재현할 수 있다