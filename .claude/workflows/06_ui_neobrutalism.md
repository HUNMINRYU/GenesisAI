---
description: UI 전반을 네오브루탈리즘 단일 규칙으로 통일하기 위한 워크플로우.
---

- Trigger
  - UI 스타일이 일관되지 않을 때

- Goal
  - 모든 UI 요소에 동일한 네오브루탈 규칙을 적용한다

- Design Rules
  - border: 2px solid #000
  - shadow: 4px 4px 0 #000
  - radius: 0

- Steps
  1. 디자인 토큰을 styles 파일에 정의한다
  2. 중복 및 인라인 스타일을 제거한다
  3. 사이드바 → 본문 순서로 적용한다

- Validation
  - 모든 컴포넌트가 동일한 테두리와 그림자를 가진다