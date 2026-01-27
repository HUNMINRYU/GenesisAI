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
        /* Colors - Neo Brutalism Palette */
        --bg-cream: #FFFDF7;
        --bg-yellow: #FFEB3B;
        --bg-mint: #A7F3D0;
        --bg-pink: #FBCFE8;
        --bg-blue: #BFDBFE;
        --bg-purple: #E9D5FF;
        --bg-white: #FFFFFF;

        /* Accents */
        --accent-red: #E11D48;
        --accent-blue: #2563EB;
        --accent-green: #059669;
        --accent-yellow: #F59E0B;
        --accent-purple: #7C3AED;

        /* Text & Borders */
        --text-black: #0F172A; /* Slate 900 for logical contrast (ui-ux-pro-max) */
        --text-gray: #475569;  /* Slate 600 for accessibility */
        --border-black: #000000;

        /* Spacing & Layout */
        --spacing-xs: 0.25rem;
        --spacing-sm: 0.5rem;
        --spacing-md: 1rem;
        --spacing-lg: 1.5rem;
        --radius-none: 0px;

        /* Shadows (Brutalist) */
        --shadow-normal: 4px 4px 0px 0px var(--border-black);
        --shadow-hover: 6px 6px 0px 0px var(--border-black);
        --shadow-active: 2px 2px 0px 0px var(--border-black);

        /* Transitions (ui-ux-pro-max preference: 150-300ms) */
        --trans-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
        --trans-smooth: 300ms cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* -------------------------------------------------------------------------- */
    /* Typography (UI/UX Pro Max: Rule 5)                                         */
    /* -------------------------------------------------------------------------- */
    /* -------------------------------------------------------------------------- */
    /* Typography (UI/UX Pro Max: Rule 5)                                         */
    /* -------------------------------------------------------------------------- */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif !important;
        color: var(--text-black) !important;
        line-height: 1.5 !important; /* Adjusted for better vertical fit */
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em !important;
        color: var(--text-black) !important;
        margin-bottom: var(--spacing-md) !important;
        line-height: 1.2 !important; /* Prevent heading overlap */
        padding: 4px 0; /* Prevent descender clipping */
    }

    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2rem !important; }
    h3 { font-size: 1.75rem !important; }

    /* -------------------------------------------------------------------------- */
    /* Layout & Base                                                              */
    /* -------------------------------------------------------------------------- */
    .stApp {
        background-color: var(--bg-cream) !important;
    }

    /* Remove default rounded corners globally for Brutalist look */
    div, button, input, select, textarea {
        border-radius: var(--radius-none) !important;
    }

    /* -------------------------------------------------------------------------- */
    /* Components: Cards                                                          */
    /* -------------------------------------------------------------------------- */
    .neo-card {
        background: var(--bg-white);
        border: 3px solid var(--border-black);
        padding: var(--spacing-lg);
        box-shadow: var(--shadow-normal);
        transition: transform var(--trans-fast), box-shadow var(--trans-fast);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 120px;
        position: relative;
        overflow: visible; /* Ensure shadows/transform don't clip */
    }

    /* Flexible Container Variant */
    .neo-container {
        background: var(--bg-white);
        border: 3px solid var(--border-black);
        padding: var(--spacing-md);
        box-shadow: var(--shadow-normal);
        margin-bottom: var(--spacing-md);
    }
    .neo-container.pink { background: var(--bg-pink); }
    .neo-container.blue { background: var(--bg-blue); }
    .neo-container.mint { background: var(--bg-mint); }
    .neo-container.yellow { background: var(--bg-yellow); }

    /* Interaction (UI/UX Pro Max: Rule 2) */
    .neo-card:hover, .neo-container:hover {
        transform: translate(-2px, -2px);
        box-shadow: var(--shadow-hover);
        cursor: pointer; /* Explicit interaction cue */
    }

    .neo-card:active, .neo-container:active {
        transform: translate(2px, 2px);
        box-shadow: var(--shadow-active);
    }

    /* Card Variants */
    .neo-card.pink { background: var(--bg-pink); }
    .neo-card.blue { background: var(--bg-blue); }
    .neo-card.mint { background: var(--bg-mint); }
    .neo-card.purple { background: var(--bg-purple); }
    .neo-card.yellow { background: var(--bg-yellow); }

    .neo-metric-icon {
        font-size: 2rem;
        margin-bottom: var(--spacing-sm);
        line-height: 1;
    }
    .neo-metric-value {
        font-size: 2rem;
        font-weight: 900;
        line-height: 1.1;
        margin-bottom: 4px;
    }
    .neo-metric-label {
        font-size: 0.85rem;
        color: var(--text-gray) !important; /* Accessible contrast */
        text-transform: uppercase;
        font-weight: 700;
        letter-spacing: 0.05em;
    }

    /* -------------------------------------------------------------------------- */
    /* Header & Sidebar                                                           */
    /* -------------------------------------------------------------------------- */
    .neo-header {
        background: var(--bg-white);
        border: 4px solid var(--border-black);
        padding: var(--spacing-lg) var(--spacing-md);
        text-align: center;
        box-shadow: 8px 8px 0px var(--border-black);
        margin-bottom: 3rem;
        position: relative;
    }

    .neo-title {
        font-size: 3.5rem !important;
        text-transform: uppercase;
        margin: 0 !important;
        text-shadow: 4px 4px 0px var(--bg-yellow); /* Depth effect */
        line-height: 1.1 !important;
    }

    .neo-subtitle {
        font-family: 'Space Grotesk', monospace !important;
        background: var(--text-black);
        color: var(--bg-white) !important;
        padding: 4px 16px;
        font-weight: 600;
        transform: rotate(-1.5deg);
        display: inline-block;
        margin-top: 8px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFF0B4 !important; /* Softer yellow */
        border-right: 3px solid var(--border-black) !important;
    }

    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {
        gap: 1rem;
    }

    .sidebar-brand {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-top: 4px;
        margin-bottom: 8px;
    }

    .sidebar-brand-title {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.6rem;
        font-weight: 800;
        line-height: 1.1;
        letter-spacing: -0.02em;
        color: var(--text-black);
        word-break: keep-all;
    }

    .sidebar-brand-sub {
        font-size: 0.9rem;
        color: var(--text-gray);
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    /* Ensure sidebar content isn't clipped */
    section[data-testid="stSidebar"] .stMarkdown h1,
    section[data-testid="stSidebar"] .stMarkdown h2,
    section[data-testid="stSidebar"] .stMarkdown h3 {
        overflow: visible;
        line-height: 1.3 !important;
    }

    /* -------------------------------------------------------------------------- */
    /* Streamlit Overrides (Inputs, Buttons, Tabs)                                */
    /* -------------------------------------------------------------------------- */

    /* Buttons */
    .stButton > button {
        background: var(--accent-red) !important;
        border: 3px solid var(--border-black) !important;
        color: white !important;
        font-weight: 800 !important;
        padding: 0.75rem 1.5rem !important; /* Prevent text clipping */
        min-height: 48px !important;
        box-shadow: var(--shadow-normal) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        transition: all var(--trans-fast) !important;
        line-height: 1.2 !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
    }

    .stButton > button:hover {
        transform: translate(-3px, -3px) !important;
        box-shadow: var(--shadow-hover) !important;
        filter: brightness(1.1);
    }

    .stButton > button:active {
        transform: translate(2px, 2px) !important;
        box-shadow: var(--shadow-active) !important;
    }

    /* Specific overrides for secondary buttons if any */
    button[kind="secondary"] {
        background: white !important;
        color: var(--text-black) !important;
    }

    /* Inputs (Text, Select) */
    .stTextInput > div > div,
    .stSelectbox > div > div,
    .stTextArea > div > div,
    .stNumberInput > div > div {
        background: white !important;
        border: 2px solid var(--border-black) !important;
        box-shadow: var(--shadow-normal) !important;
        color: var(--text-black) !important;
        min-height: 48px !important;
        padding: 0 !important;
    }

    .stTextInput input,
    .stTextArea textarea,
    .stNumberInput input,
    .stSelectbox input {
        line-height: 1.4 !important;
        padding: 0.65rem 0.75rem !important;
        height: auto !important;
        box-sizing: border-box !important;
    }

    /* BaseWeb input wrapper (prevents descender clipping) */
    [data-baseweb="input"],
    [data-baseweb="base-input"] {
        min-height: 48px !important;
        align-items: center !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }

    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input {
        line-height: 1.4 !important;
        padding: 0.65rem 0.75rem !important;
        height: auto !important;
        box-sizing: border-box !important;
    }

    /* Fix label clipping */
    .stTextInput label, .stSelectbox label, .stTextArea label, .stNumberInput label {
        font-weight: 700 !important;
        color: var(--text-black) !important;
        margin-bottom: 4px !important;
        display: block;
        line-height: 1.4 !important;
    }

    .stTextInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within {
        box-shadow: var(--shadow-hover) !important;
        transform: translate(-1px, -1px);
        border-color: var(--accent-blue) !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding-top: 10px !important;
        padding-bottom: 10px !important; /* Add padding for shadow */
        overflow: visible !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: white !important;
        border: 2px solid var(--border-black) !important;
        padding: 8px 20px !important;
        box-shadow: 2px 2px 0 var(--border-black) !important;
        transition: all var(--trans-fast) !important;
        opacity: 0.7;
        margin-bottom: 4px; /* Separation */
    }

    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-2px);
        opacity: 1;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: var(--bg-yellow) !important;
        opacity: 1;
        box-shadow: 4px 4px 0 var(--border-black) !important;
        transform: translateY(-3px);
    }

    /* Alerts (Info, Success, Error) */
    .stAlert {
        border: 3px solid var(--border-black) !important;
        box-shadow: var(--shadow-normal) !important;
        background-color: white !important; /* Reset default background */
    }

    div[data-baseweb="notification"] {
        background-color: white !important;
    }

    .stSuccess { background-color: var(--bg-mint) !important; }
    .stInfo    { background-color: var(--bg-blue) !important; }
    .stWarning { background-color: var(--bg-yellow) !important; }
    .stError   { background-color: var(--bg-pink) !important; }

    /* Align alerts with labeled inputs inside horizontal blocks */
    .stHorizontalBlock .stAlert {
        /* Align alert top border with input top border (accounting for label height) */
        margin-top: calc(1.4em + 6px) !important;
    }
    .stHorizontalBlock .stAlertContainer {
        min-height: 48px !important;
        display: flex !important;
        align-items: center !important;
    }

    /* -------------------------------------------------------------------------- */
    /* A/B Test Panels                                                            */
    /* -------------------------------------------------------------------------- */
    .ab-panel-marker {
        display: block;
        height: 0;
        overflow: hidden;
        margin: 0;
        padding: 0;
    }

    /* Avoid double borders by only styling the innermost block that holds the marker */
    .stColumn [data-testid="stVerticalBlock"]:has([data-testid="stVerticalBlock"] .ab-panel-a),
    .stColumn [data-testid="stVerticalBlock"]:has([data-testid="stVerticalBlock"] .ab-panel-b) {
        border: 0 !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin-bottom: 0 !important;
        background: transparent !important;
    }

    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-a):not(:has([data-testid="stVerticalBlock"] .ab-panel-a)),
    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-b):not(:has([data-testid="stVerticalBlock"] .ab-panel-b)) {
        border: 3px solid var(--border-black) !important;
        box-shadow: var(--shadow-normal) !important;
        padding: var(--spacing-md) !important;
        margin-bottom: var(--spacing-md) !important;
        background: var(--bg-white) !important;
    }

    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-a):not(:has([data-testid="stVerticalBlock"] .ab-panel-a)) {
        background: var(--bg-pink) !important;
    }

    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-b):not(:has([data-testid="stVerticalBlock"] .ab-panel-b)) {
        background: var(--bg-blue) !important;
    }

    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-a) .neo-container,
    .stColumn [data-testid="stVerticalBlock"]:has(.ab-panel-b) .neo-container {
        border: 0 !important;
        box-shadow: none !important;
        background: transparent !important;
    }

    /* -------------------------------------------------------------------------- */
    /* Animations                                                                 */
    /* -------------------------------------------------------------------------- */
    @keyframes slideUpFade {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .neo-animate-slide-up {
        animation: slideUpFade 0.6s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
    }

    /* -------------------------------------------------------------------------- */
    /* Terminal Log Viewer                                                         */
    /* -------------------------------------------------------------------------- */
    .terminal-container {
        background: #1a1a2e;
        border: 3px solid var(--border-black);
        box-shadow: var(--shadow-normal);
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        height: 400px;
        overflow-y: auto;
        padding: 0;
        margin: 16px 0;
    }

    .terminal-header {
        background: #16213e;
        padding: 8px 16px;
        border-bottom: 2px solid #0f3460;
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: sticky;
        top: 0;
        z-index: 10;
    }

    .terminal-dots {
        display: flex;
        gap: 6px;
    }

    .terminal-dot {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        border: 1px solid rgba(255,255,255,0.2);
    }

    .terminal-dot.red { background: #ff5f56; }
    .terminal-dot.yellow { background: #ffbd2e; }
    .terminal-dot.green { background: #27c93f; }

    .terminal-title {
        color: #00ff88;
        font-weight: bold;
        font-size: 0.9rem;
    }

    .terminal-body {
        padding: 16px;
        color: #e0e0e0;
        font-size: 0.85rem;
        line-height: 1.6;
    }

    .log-line {
        padding: 2px 0;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .log-timestamp {
        color: #6b7280;
    }

    .log-level-info { color: #22c55e; }
    .log-level-warning { color: #f59e0b; }
    .log-level-error { color: #ef4444; }
    .log-level-debug { color: #06b6d4; }
    .log-level-critical { color: #ec4899; }

    .log-emoji {
        margin-right: 4px;
    }

    .log-message {
        color: #e0e0e0;
    }

    /* Terminal Scrollbar */
    .terminal-container::-webkit-scrollbar {
        width: 8px;
    }

    .terminal-container::-webkit-scrollbar-track {
        background: #1a1a2e;
    }

    .terminal-container::-webkit-scrollbar-thumb {
        background: #4a4a6a;
        border-radius: 4px;
    }

    .terminal-container::-webkit-scrollbar-thumb:hover {
        background: #6a6a8a;
    }

    .log-empty {
        color: #6b7280;
        font-style: italic;
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


def render_neo_card_html(
    title: str, content: str, color: str = "", icon: str = ""
) -> str:
    """일반 콘텐츠용 네오브루탈리즘 카드 HTML 생성"""
    icon_html = (
        f'<div class="neo-metric-icon" style="font-size:1.5rem; text-align:left;">{icon}</div>'
        if icon
        else ""
    )
    return f"""
    <div class="neo-container {color}" style="height: 100%; display: flex; flex-direction: column;">
        {icon_html}
        <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem; border-bottom: 2px solid black;">{title}</h3>
        <div style="flex-grow: 1;">{content}</div>
    </div>
    """


def render_feature_list(items: list[str]) -> str:
    """네오브루탈리즘 특징 리스트 렌더링"""
    # UI/UX Pro Max: 리스트 아이템 간격 및 가독성 최적화
    html = '<div style="display: flex; flex-direction: column; gap: 8px;">'
    for item in items:
        html += f"""
        <div class="neo-step active" style="background: white;">
            <span class="neo-step-icon">✔</span>
            <span class="neo-step-label">{item}</span>
        </div>
        """
    html += "</div>"
    return html


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
    # 진행률 표시줄의 시각적 명확성 강화
    label_text = label if label else f"{progress}%"
    return f"""
    <div class="neo-progress">
        <div class="neo-progress-track">
            <div class="neo-progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="neo-progress-text">{label_text}</div>
    </div>
    """
