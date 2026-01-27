---
description: 네오브루탈 UI에서 발생하는 미세한 CSS 깨짐 현상을 해결한다.
---

- Trigger
  - 테두리가 한쪽만 얇아질 때

- Goal
  - 모든 방향의 테두리를 동일하게 만든다

- Steps
  1. computed style로 원인을 추적한다
  2. CSS 우선순위 충돌을 해결한다
  3. 최소한의 !important만 사용한다

- Validation
  - 모든 테두리가 동일한 두께로 표시된다