"""
네오브루탈리즘 스타일 시스템
"""

import streamlit as st


def inject_neobrutalism_css() -> None:
    """네오브루탈리즘 스타일 CSS 주입"""
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

    :root {
        --bg-cream: #FFFDF7;
        --bg-yellow: #FFEB3B;
        --bg-mint: #A7F3D0;
        --bg-pink: #FBCFE8;
        --bg-blue: #BFDBFE;
        --bg-purple: #E9D5FF;

        --accent-red: #E11D48;
        --accent-blue: #2563EB;
        --accent-green: #059669;
        --accent-yellow: #F59E0B;
        --accent-purple: #7C3AED;

        --text-black: #0F172A;
        --text-gray: #334155;
        --border-black: #000000;

        --shadow-hard: 4px 4px 0px 0px var(--border-black);
        --shadow-hover: 6px 6px 0px 0px var(--border-black);
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes popIn {
        0% { transform: scale(0.9); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
    }

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        color: var(--text-black) !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
    }

    .stApp {
        background-color: var(--bg-cream) !important;
        opacity: 0.98;
    }

    .neo-card, .neo-header, .neo-footer {
        animation: fadeIn 0.5s ease-out forwards;
    }

    .neo-header {
        text-align: center;
        padding: 40px 20px;
        margin-bottom: 30px;
        background: white;
        border: 3px solid var(--border-black);
        box-shadow: var(--shadow-hard);
        position: relative;
        overflow: hidden;
    }

    .neo-header::before {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 8px;
        background: repeating-linear-gradient(
            45deg,
            var(--accent-yellow),
            var(--accent-yellow) 10px,
            var(--text-black) 10px,
            var(--text-black) 20px
        );
    }

    .neo-title {
        font-size: 3rem !important;
        text-transform: uppercase;
        margin: 0 !important;
        text-shadow: 2px 2px 0px var(--bg-yellow);
    }

    .neo-subtitle {
        font-size: 1.1rem !important;
        font-family: 'Space Grotesk', monospace !important;
        background: var(--text-black);
        color: white !important;
        display: inline-block;
        padding: 4px 12px;
        margin-top: 10px;
        transform: rotate(-1deg);
    }

    section[data-testid="stSidebar"] {
        background: rgb(255, 240, 180) !important;
        border-right: 3px solid var(--border-black) !important;
        width: 280px !important;
    }

    /* 사이드바 요소 패딩 */
    section[data-testid="stSidebar"] > div {
        padding-top: 1rem !important;
    }

    .neo-card {
        background: white;
        border: 2px solid var(--border-black);
        border-radius: 0;
        padding: 12px;
        box-shadow: 4px 4px 0 var(--border-black);
        transition: all 0.2s ease;
        text-align: center;
        min-height: 90px;
        box-sizing: border-box !important;
        width: calc(100% - 6px) !important;
    }

    .neo-card:hover {
        transform: translate(-2px, -2px);
        box-shadow: 6px 6px 0 var(--border-black);
    }

    .neo-card.pink { background: var(--bg-pink); }
    .neo-card.blue { background: var(--bg-blue); }
    .neo-card.mint { background: var(--bg-mint); }
    .neo-card.purple { background: var(--bg-purple); }
    .neo-card.yellow { background: var(--bg-yellow); }

    .neo-metric-icon { font-size: 1.4rem; margin-bottom: 4px; }
    .neo-metric-value { font-size: 1.5rem; font-weight: 700; color: var(--text-black) !important; }
    .neo-metric-label { font-size: 0.7rem; color: var(--text-gray) !important; text-transform: uppercase; font-weight: 600; }

    .neo-progress {
        background: var(--bg-cream);
        border: 2px solid var(--border-black);
        padding: 12px;
        box-shadow: 4px 4px 0 var(--border-black);
        margin: 8px 0;
        border-radius: 0 !important;
        box-sizing: border-box !important;
        width: calc(100% - 6px) !important;
    }

    .neo-progress-track { background: white; border: 2px solid var(--border-black); height: 16px; overflow: hidden; border-radius: 0 !important; }
    .neo-progress-fill { height: 100%; background: var(--accent-green); transition: width 0.5s ease; border-right: 2px solid var(--border-black); border-radius: 0 !important; }
    .neo-progress-text { text-align: center; margin-top: 8px; font-size: 0.9rem; font-weight: 700; color: var(--text-black) !important; }

    .neo-step {
        display: flex;
        align-items: center;
        padding: 8px 12px;
        margin: 4px 0;
        background: #f1f5f9;
        border: 2px solid var(--border-black);
        box-shadow: 2px 2px 0 var(--border-black);
        border-radius: 0 !important;
        box-sizing: border-box !important;
        width: calc(100% - 6px) !important;
    }

    .neo-step.complete { background: var(--bg-mint); }
    .neo-step.active { background: var(--bg-blue); box-shadow: 4px 4px 0 var(--border-black); transform: translate(-1px, -1px); }
    .neo-step-icon { font-size: 1rem; margin-right: 10px; font-weight: 800; border: 2px solid var(--border-black); width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; background: white; box-shadow: 2px 2px 0 var(--border-black); }
    .neo-step-label { font-weight: 700; color: var(--text-black) !important; font-size: 0.9rem; }

    /* Selectbox 스타일 */
    .stSelectbox > div > div {
        background: white !important;
        border: 2px solid var(--border-black) !important;
        border-radius: 0 !important;
        box-shadow: 4px 4px 0 var(--border-black) !important;
        min-height: 42px !important;
    }

    /* 드롭다운 메뉴 (옵션 리스트) */
    ul[data-baseweb="menu"] {
        background: white !important;
        border: 2px solid var(--border-black) !important;
        border-radius: 0 !important;
        box-shadow: 4px 4px 0 var(--border-black) !important;
        padding: 0 !important;
    }

    ul[data-baseweb="menu"] > li {
        border-bottom: 2px solid var(--border-black) !important;
        margin: 0 !important;
        padding: 10px 12px !important;
        color: var(--text-black) !important;
        font-weight: 500 !important;
    }
    ul[data-baseweb="menu"] > li:last-child { border-bottom: none !important; }
    ul[data-baseweb="menu"] > li[aria-selected="true"],
    ul[data-baseweb="menu"] > li:hover { background: var(--bg-yellow) !important; font-weight: 700 !important; }

    /* Container 스타일 (bordered) */
    div[data-testid="stVerticalBlock"] > div:has(> div.stContainer) {
        border: 2px solid var(--border-black) !important;
        border-radius: 0 !important;
        box-shadow: 4px 4px 0 var(--border-black) !important;
        padding: 16px !important;
        background: white !important;
        margin-bottom: 16px !important;
    }

    .stButton > button {
        background: var(--accent-red) !important;
        border: 2px solid var(--border-black) !important;
        border-radius: 0 !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 10px 20px !important;
        box-shadow: 4px 4px 0 var(--border-black) !important;
        text-transform: uppercase !important;
    }

    .stButton > button:hover {
        transform: translate(-2px, -2px) !important;
        box-shadow: 6px 6px 0 var(--border-black) !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        background: white !important;
        border: 2px solid var(--border-black) !important;
        box-shadow: 4px 4px 0 var(--border-black) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: white !important;
        border-right: 2px solid var(--border-black) !important;
        font-weight: 600 !important;
        padding: 10px 16px !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--accent-yellow) !important;
        font-weight: 700 !important;
    }

    .stSuccess { background: var(--bg-mint) !important; border: 2px solid var(--border-black) !important; }
    .stInfo { background: var(--bg-blue) !important; border: 2px solid var(--border-black) !important; }
    .stWarning { background: var(--bg-yellow) !important; border: 2px solid var(--border-black) !important; }
    .stError { background: var(--bg-pink) !important; border: 2px solid var(--border-black) !important; }

    .neo-footer { text-align: center; padding: 16px; margin-top: 12px; }
    .neo-footer-badge {
        display: inline-block;
        background: var(--accent-purple);
        color: white !important;
        padding: 6px 16px;
        border: 2px solid var(--border-black);
        box-shadow: 4px 4px 0 var(--border-black);
        font-weight: 700;
        font-size: 0.8rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """네오브루탈리즘 헤더 렌더링"""
    st.markdown(
        """
    <div class="neo-header">
        <h1 class="neo-title">GENESIS AI</h1>
        <div class="neo-subtitle">숏폼 콘텐츠 자동화 파이프라인</div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """네오브루탈리즘 푸터 렌더링"""
    st.markdown(
        """
    <div class="neo-footer">
        <span class="neo-footer-badge">Vertex AI + Gemini + Veo 3.1 Powered</span>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_metric_card(icon: str, value: str, label: str, color: str = "") -> str:
    """네오브루탈리즘 메트릭 카드 렌더링"""
    return f"""
    <div class="neo-card {color}" style="animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards;">
        <div class="neo-metric-icon">{icon}</div>
        <div class="neo-metric-value">{value}</div>
        <div class="neo-metric-label">{label}</div>
    </div>
    """


def render_step_item(icon: str, label: str, status: str = "") -> str:
    """네오브루탈리즘 스텝 아이템 렌더링"""
    return f"""
    <div class="neo-step {status}">
        <span class="neo-step-icon">{icon}</span>
        <span class="neo-step-label">{label}</span>
    </div>
    """


def render_progress_bar(progress: int, label: str = "") -> str:
    """네오브루탈리즘 프로그레스 바 렌더링"""
    return f"""
    <div class="neo-progress">
        <div class="neo-progress-track">
            <div class="neo-progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="neo-progress-text">{label if label else f"{progress}%"}</div>
    </div>
    """
