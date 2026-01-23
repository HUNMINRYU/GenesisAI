# 🚀 Genesis AI Studio (Refactored)

**Genesis AI Studio**는 AI 기반 마케팅 자동화 솔루션의 리팩토링 버전입니다.  
객체 지향 설계 원칙(SOLID)을 적용하여 유지보수성과 확장성을 강화했으며, **Neobrutalism Design** 시스템을 도입하여 강렬하고 직관적인 사용자 경험을 제공합니다.

---

## ✨ Key Features

### 1. 🏗️ SOLID Architecture
- **SRP (Single Responsibility)**: 각 모듈(Presentation, Domain, Infrastructure)의 역할 분리
- **DIP (Dependency Inversion)**: 추상화(Interface)에 의존하는 유연한 아키텍처
- **Clean Architecture**: 도메인 로직과 외부 의존성(Streamlit, API)의 철저한 분리

### 2. 🎨 Neobrutalism UI System
- **Bold & Vivid**: 고대비 색상과 굵은 테두리를 활용한 강렬한 디자인
- **Responsive Components**: 커스텀 CSS (`neobrutalism.py`)를 통해 Streamlit의 한계를 넘는 반응형 UI 구현
- **Visual Feedback**: Pain Points(Pink) / Gain Points(Mint) / Viral Hooks(Yellow) 등 데이터를 색상으로 시각화

### 3. 🧠 Smart Pipeline
- **Data Collection**: YouTube, Naver 쇼핑 데이터 자동 수집
- **AI Analysis**: 타겟 페르소나 분석 및 바이럴 마케팅 전략 수립
- **Content Generation**: 최적화된 썸네일 및 숏폼 비디오 대본 생성

---

## 📂 Project Structure

```bash
src/genesis_ai/
├── config/             # 설정 및 상수 관리
├── core/               # 도메인 모델 & 인터페이스 (Business Logic)
├── infrastructure/     # 외부 서비스 연동 (YouTube, Gemini, Naver API)
├── presentation/       # UI/UX 레이어 (Streamlit App)
│   └── styles/         # Neobrutalism 스타일 시스템
└── services/           # 유스케이스 및 서비스 오케스트레이션
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Streamlit

### Installation

```bash
# Clone the repository
git clone https://github.com/HUNMINRYU/GenesisAI.git

# Install dependencies
pip install -r requirements.txt
```

### Running the App

```bash
# Run the Streamlit application
python run.py
```

---

## 🛠️ Tech Stack

- **Framework**: Streamlit
- **Language**: Python 3.13
- **Design System**: Custom CSS (Neobrutalism)
- **AI Model**: Google Gemini Pro (via Vertex AI)
