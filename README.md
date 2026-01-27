# 🚀 Genesis AI (v3.0 Refactored)

**Genesis AI**는 데이터 기반의 마케팅 의사결정을 지원하는 **AI 에이전트 시스템**입니다.  
유튜브 댓글과 검색 데이터를 분석하여 **"팔리는 마케팅 포인트"**를 찾아내고, 이를 바탕으로 구매 전환율(Conversion)을 극대화하는 전략을 제안합니다.

특히, 트위터(X)의 추천 알고리즘 철학을 이식한 **X-Algorithm Pipeline**을 탑재하여, 단순한 감정 분석을 넘어 **"실제 인게이지먼트(Engagement)를 유발하는 핵심 댓글"**을 발굴합니다.

---

## ✨ Key Features (주요 기능)

### 1. 🔍 X-Algorithm Pipeline (New!)
사용자 데이터를 단순 분석하는 것을 넘어, **Engagement Score(참여 점수)**를 기반으로 가장 가치 있는 인사이트를 추출합니다.

- **Pipeline Stages**:
  1. **Source**: YouTube 댓글, 네이버 리뷰 등 Raw Data 수집
  2. **Hydration (All-Important)**: Gemini(LLM)를 사용해 각 댓글의 `구매 의도`, `답글 유발성`, `구체성` 등 Rich Feature 추출
  3. **Filter**: 스팸, 단순 비방 등 저품질 데이터 사전 차단
  4. **Scorer (Linear Weighting)**: 다양한 Feature에 가중치를 부여하여 Engagement Probability 계산
  5. **Selector**: 상위 n%의 핵심 인사이트(Top Insights) 선정 및 시각화

### 2. 🏗️ SOLID Architecture
유지보수성과 확장성을 고려한 견고한 아키텍처로 설계되었습니다.

- **SRP (Single Responsibility)**: 각 모듈의 역할 분리
- **DIP (Dependency Inversion)**: 인터페이스 기반 설계로 외부 의존성(Gemini, YouTube API 등) 교체 용이

### 3. 🎨 Neobrutalism UI System
강렬하고 직관적인 **Neobrutalism 디자인**을 적용하여 데이터의 가독성을 극대화했습니다.

- **Visual Feedback**: 긍정(Mint), 부정(Pink), 중요 인사이트(Yellow) 등 색상 기반의 직관적 피드백
- **Interactive**: 반응형 카드 UI 및 데이터 시각화

---

## 📂 Project Structure

```bash
src/genesis_ai/

├── config/             # 설정 및 상수 관리
├── core/               # 도메인 엔티티 & 인터페이스 (Business Logic)
├── infrastructure/     # 외부 서비스 어댑터 (Gemini, YouTube API, Naver API)
├── presentation/       # UI/UX 레이어 (Streamlit Components)
│   ├── styles/         # Neobrutalism 디자인 시스템
│   └── tabs/           # 기능별 탭 (분석, 썸네일, 영상 스크립트 등)
└── services/           # 애플리케이션 비즈니스 로직
    ├── pipeline/       # 🚀 X-Algorithm 파이프라인 엔진 (Orchestrator, Stages)
    └── ...
```

---

## 🚀 워크플로우 (User Journey)

1. **데이터 수집 (Data Collection)**
   - YouTube URL 또는 제품명을 입력하여 실제 고객의 목소리를 수집합니다.
2. **AI 심층 분석 (Deep Analysis)**
   - **X-Algorithm**이 작동하여 수천 개의 댓글 중 '진짜 인사이트'를 걸러냅니다.
   - 구매 버튼을 누르게 만드는 결정적 요인(Buying Factors)과 고객의 숨은 불만(Deep Pain Points)을 찾아냅니다.
3. **전략 수립 (Strategy Building)**
   - 타겟 페르소나를 정의하고, 차별화 포인트(USP)를 도출합니다.
4. **콘텐츠 제작 (Content Creation)**
   - CTR을 높이는 **썸네일** 문구와 디자인을 제안합니다.
   - 숏폼(Shorts/Reels) 영상용 **대본**을 자동 생성합니다.

---

## 🛠️ Tech Stack

- **Framework**: Streamlit (Python 3.10+)
- **AI Model**: Google Gemini Pro 1.5 (via Vertex AI / Studio)
- **Architecture**: Clean Architecture + Pipeline Pattern
- **Design System**: Custom CSS (Neobrutalism)
- **Testing**: Pytest

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10 이상
- Google Gemini API Key 필요

### 2. Installation

```bash
# 1. 레포지토리 클론
git clone https://github.com/HUNMINRYU/GenesisAI.git

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
```

### 3. Running the App

```bash
python run.py
```

---

## 🔐 Environment Variables

필수:
- `GOOGLE_CLOUD_PROJECT_ID`
- `GOOGLE_API_KEY`
- `NAVER_CLIENT_ID`
- `NAVER_CLIENT_SECRET`

선택:
- `GOOGLE_CLOUD_LOCATION` (기본값: `us-central1`)
- `GOOGLE_APPLICATION_CREDENTIALS` (GCP 서비스 계정 경로)
- `GCS_BUCKET_NAME` (GCS 업로드 사용 시)
- `NOTION_API_KEY` (Notion 내보내기 사용 시)
- `NOTION_DATABASE_ID`
- `OUTPUT_DIR` (결과물 저장 경로)

---

## 🧰 운영/배포

운영 환경 설정, 모니터링, 트러블슈팅은 `docs/OPERATIONS.md`를 참고하세요.

## 🏗️ 아키텍처

구성 및 데이터 흐름은 `docs/ARCHITECTURE.md`를 참고하세요.
