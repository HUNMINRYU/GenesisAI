"""
Genesis AI Studio - Streamlit 메인 애플리케이션
SOLID 원칙 기반 리팩토링 버전
"""

import streamlit as st

from genesis_ai.config.products import get_product_names, get_product_by_name
from genesis_ai.config.settings import get_settings
from genesis_ai.core.models import PipelineStep
from genesis_ai.utils.logger import log_app_start, log_tab_load
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.styles.neobrutalism import (
    inject_neobrutalism_css,
    render_footer,
    render_header,
    render_metric_card,
)


def setup_page() -> None:
    """페이지 설정"""
    st.set_page_config(
        page_title="Genesis AI Studio",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def setup_environment() -> None:
    """환경 설정"""
    try:
        settings = get_settings()
        settings.setup_environment()
    except Exception as e:
        st.warning(f"환경 설정 로드 실패: {e}. .env 파일을 확인해주세요.")


def render_sidebar() -> dict | None:
    """사이드바 렌더링 (Enhanced with Neo-Progress & Steps)"""
    from genesis_ai.presentation.styles.neobrutalism import (
        render_progress_bar,
        render_step_item,
    )

    with st.sidebar:
        st.markdown("### 🛡️ 제네시스 AI")
        st.caption("데이터 수집 → AI 분석 → 콘텐츠 생성")
        st.markdown("---")

        # 제품 선택
        st.markdown("#### 🛒 제품 선택")
        product_names = get_product_names()
        selected_name = st.selectbox(
            "제품 선택",
            options=product_names,
            index=0,
            key="product_selector",
            label_visibility="collapsed",
        )

        product = get_product_by_name(selected_name)
        if product:
            SessionManager.set_selected_product(product.to_dict())

            # 제품 정보 카드 (Yellow)
            st.markdown(
                f"""
            <div class="neo-card yellow" style="text-align: left; padding: 10px; min-height: auto;">
                <div style="font-size: 0.85rem; opacity: 0.9;">{product.description}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        st.markdown("---")

        # 진행률 표시
        progress = SessionManager.get_pipeline_progress()
        st.markdown("#### 📊 진행률")
        st.markdown(
            render_progress_bar(progress.percentage, progress.message or "대기 중"),
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # 단계 표시
        st.markdown("#### 📍 단계")
        current_step = progress.current_step if hasattr(progress, "current_step") else 0

        steps = [
            ("▶️", "데이터 수집"),
            ("02", "AI 분석"),
            ("03", "콘텐츠 생성"),
        ]
        # 현재 단계 인덱스 매핑
        current_step_idx = 0
        if isinstance(current_step, int):
            current_step_idx = current_step
        else:
            # Enum 값을 기반으로 인덱스 결정
            step_val = (
                current_step.value
                if hasattr(current_step, "value")
                else str(current_step)
            )

            if step_val in [
                PipelineStep.INITIALIZED.value,
                PipelineStep.DATA_COLLECTION.value,
                PipelineStep.YOUTUBE_COLLECTION.value,
                PipelineStep.NAVER_COLLECTION.value,
            ]:
                current_step_idx = 0
            elif step_val == PipelineStep.STRATEGY_GENERATION.value:
                current_step_idx = 1
            elif step_val in [
                PipelineStep.THUMBNAIL_CREATION.value,
                PipelineStep.VIDEO_GENERATION.value,
                PipelineStep.UPLOAD.value,
                PipelineStep.COMPLETED.value,
            ]:
                current_step_idx = 2

        for i, (icon, label) in enumerate(steps):
            status = (
                "active"
                if i == current_step_idx
                else ("complete" if i < current_step_idx else "")
            )
            st.markdown(render_step_item(icon, label, status), unsafe_allow_html=True)

        st.markdown("---")

        # 리셋 버튼
        if st.button("🔄 세션 초기화", use_container_width=True):
            SessionManager.reset()
            st.rerun()

        return product.to_dict() if product else None


def render_metrics() -> None:
    """메트릭 카드 렌더링"""
    collected_data = SessionManager.get_collected_data()
    progress = SessionManager.get_pipeline_progress()

    video_count = 0
    if collected_data and "videos" in collected_data:
        video_count = len(collected_data.get("videos", []))

    prompt_status = "대기" if not SessionManager.has_strategy() else "완료"
    render_status = "대기"
    if SessionManager.get("generated_thumbnail"):
        render_status = "완료"

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            render_metric_card("📹", str(video_count), "수집된 영상", "blue"),
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            render_metric_card("📝", prompt_status, "프롬프트 상태", "mint"),
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            render_metric_card("🎬", render_status, "렌더링 상태", "pink"),
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            render_metric_card("📊", f"{progress.percentage}%", "진행률", "purple"),
            unsafe_allow_html=True,
        )


def render_tabs() -> None:
    """탭 렌더링"""
    tab_names = [
        "🚀 파이프라인",
        "📺 YouTube",
        "🛒 네이버",
        "📊 분석",
        "🖼️ 썸네일",
        "🎬 비디오",
        "📄 리포트",
    ]

    tabs = st.tabs(tab_names)

    with tabs[0]:
        log_tab_load("파이프라인")
        render_pipeline_tab()

    with tabs[1]:
        log_tab_load("YouTube")
        render_youtube_tab()

    with tabs[2]:
        log_tab_load("네이버")
        render_naver_tab()

    with tabs[3]:
        log_tab_load("분석")
        render_analysis_tab()

    with tabs[4]:
        log_tab_load("썸네일")
        render_thumbnail_tab()

    with tabs[5]:
        log_tab_load("비디오")
        render_video_tab()

    with tabs[6]:
        log_tab_load("리포트")
        render_report_tab()


def render_pipeline_tab() -> None:
    """파이프라인 탭"""
    st.markdown("### 🚀 자동화 파이프라인")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    st.info(f"선택된 제품: **{product.get('name', 'N/A')}**")

    with st.expander("⚙️ 파이프라인 설정", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            youtube_count = st.slider("YouTube 검색 수", 1, 10, 3)
            include_comments = st.checkbox("댓글 분석 포함", value=True)
        with c2:
            naver_count = st.slider("네이버 쇼핑 검색 수", 5, 30, 10)
            generate_video = st.checkbox("비디오 생성", value=True)

    if st.button("🚀 파이프라인 실행", use_container_width=True, type="primary"):
        _execute_pipeline(
            product=product,
            youtube_count=youtube_count,
            naver_count=naver_count,
            include_comments=include_comments,
            generate_video=generate_video,
        )

    # 이전 실행 결과 표시
    _display_pipeline_result()


def _execute_pipeline(
    product: dict,
    youtube_count: int,
    naver_count: int,
    include_comments: bool,
    generate_video: bool,
) -> None:
    """파이프라인 실행 로직"""
    from genesis_ai.core.models import PipelineConfig, PipelineProgress
    from genesis_ai.infrastructure.factories import get_pipeline_service

    # 설정 생성
    config = PipelineConfig(
        youtube_count=youtube_count,
        naver_count=naver_count,
        include_comments=include_comments,
        generate_video=generate_video,
        generate_thumbnail=True,
    )

    # 진행 상황 표시용 placeholder
    status_container = st.status("파이프라인 실행 중...", expanded=True)

    def progress_callback(progress: PipelineProgress) -> None:
        """진행 상황 콜백"""
        status_container.update(label=f"진행률: {progress.percentage}%")
        status_container.write(f"📍 {progress.message}")

    try:
        # 파이프라인 서비스 가져오기
        pipeline_service = get_pipeline_service()

        # 파이프라인 실행
        result = pipeline_service.execute(
            product=product,
            config=config,
            progress_callback=progress_callback,
        )

        # 결과 저장
        if result.success:
            status_container.update(label="✅ 파이프라인 완료!", state="complete")

            # 세션에 결과 저장
            if result.collected_data:
                SessionManager.set(
                    "collected_data",
                    {
                        "youtube_data": result.collected_data.youtube_data,
                        "naver_data": result.collected_data.naver_data,
                        "pain_points": result.collected_data.pain_points,
                        "gain_points": result.collected_data.gain_points,
                        "videos": result.collected_data.youtube_data.get("videos", [])
                        if result.collected_data.youtube_data
                        else [],
                    },
                )
            if result.strategy:
                SessionManager.set("marketing_strategy", result.strategy)
            if result.generated_content:
                if result.generated_content.thumbnail_data:
                    SessionManager.set(
                        "generated_thumbnail", result.generated_content.thumbnail_data
                    )
                if result.generated_content.video_url:
                    SessionManager.set(
                        "generated_video_url", result.generated_content.video_url
                    )

            # 결과 저장 (전체)
            SessionManager.set(
                "pipeline_result",
                {
                    "success": result.success,
                    "product_name": result.product_name,
                    "duration_seconds": result.duration_seconds,
                    "executed_at": result.executed_at.isoformat(),
                },
            )

            st.success(
                f"파이프라인 실행 완료! (소요 시간: {result.duration_seconds:.1f}초)"
            )
        else:
            status_container.update(label="❌ 파이프라인 실패", state="error")
            st.error(f"파이프라인 실행 실패: {result.error_message}")

    except Exception as e:
        status_container.update(label="❌ 오류 발생", state="error")
        st.error(f"파이프라인 실행 중 오류: {e}")


def _display_pipeline_result() -> None:
    """이전 파이프라인 실행 결과 표시 (Enhanced with Neo-Cards)"""
    result = SessionManager.get("pipeline_result")
    if not result:
        return

    st.markdown("---")
    st.markdown("#### 📊 마지막 실행 결과")

    c1, c2, c3 = st.columns(3)
    with c1:
        status = "✅ 성공" if result.get("success") else "❌ 실패"
        st.metric("상태", status)
    with c2:
        st.metric("제품", result.get("product_name", "N/A"))
    with c3:
        duration = result.get("duration_seconds", 0)
        st.metric("소요 시간", f"{duration:.1f}초")

    # 수집된 데이터 결과 표시 (Pain & Gain Points)
    collected_data = SessionManager.get("collected_data")
    if collected_data:
        pain_points = collected_data.get("pain_points", [])
        gain_points = collected_data.get("gain_points", [])

        if pain_points or gain_points:
            c1, c2 = st.columns(2)

            # Pain Points (Pink Card)
            with c1:
                if pain_points:
                    st.markdown(
                        """
                    <div class="neo-card pink" style="text-align: left; padding: 15px; margin-bottom: 20px;">
                        <div class="neo-metric-label" style="color:#550000 !important;">😡 PAIN POINTS</div>
                        <ul style="padding-left: 20px; margin-top: 10px; font-weight: 500;">
                    """,
                        unsafe_allow_html=True,
                    )
                    for point in pain_points[:5]:  # 최대 5개 표시
                        text = (
                            point
                            if isinstance(point, str)
                            else point.get("text", str(point))
                        )
                        st.markdown(f"<li>{text}</li>", unsafe_allow_html=True)
                    st.markdown("</ul></div>", unsafe_allow_html=True)

            # Gain Points (Mint Card)
            with c2:
                if gain_points:
                    st.markdown(
                        """
                    <div class="neo-card mint" style="text-align: left; padding: 15px; margin-bottom: 20px;">
                        <div class="neo-metric-label" style="color:#004400 !important;">😍 GAIN POINTS</div>
                        <ul style="padding-left: 20px; margin-top: 10px; font-weight: 500;">
                    """,
                        unsafe_allow_html=True,
                    )
                    for point in gain_points[:5]:  # 최대 5개 표시
                        text = (
                            point
                            if isinstance(point, str)
                            else point.get("text", str(point))
                        )
                        st.markdown(f"<li>{text}</li>", unsafe_allow_html=True)
                    st.markdown("</ul></div>", unsafe_allow_html=True)

    # 마케팅 전략 결과 표시
    strategy = SessionManager.get("marketing_strategy")
    if strategy:
        _display_strategy_results(strategy)


def _display_strategy_results(strategy: dict) -> None:
    """마케팅 전략 결과를 컬러 카드로 표시"""

    # 1. 타겟 페르소나 (Purple Card)
    if "target_persona" in strategy:
        with st.expander("👤 **Target Persona Deep Dive**", expanded=True):
            p = strategy["target_persona"]
            st.markdown(
                f"""
            <div class="neo-card purple" style="text-align: left; padding: 15px; margin-bottom: 15px;">
                <div class="neo-metric-label" style="color:#550055 !important;">TARGET PERSONA</div>
                <div style="font-size: 1.1rem; font-weight: 700;">🎯 {p.get("age", "N/A")}</div>
                <div style="margin-top: 8px; font-size: 0.95rem; opacity: 0.9;">💡 {p.get("description", "")}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**😱 핵심 두려움 (Pain Points)**")
                for pp in p.get("pain_points", [])[:3]:
                    st.info(f"{pp}")
            with c2:
                st.markdown("**🔥 궁극적 욕망 (Desires)**")
                for d in p.get("desires", [])[:3]:
                    st.success(f"{d}")

    # 2. 바이럴 후킹 (Yellow Card)
    if "hooking_points" in strategy:
        with st.expander("⚡ **Viral Hooks (X-Algorithm Ranked)**", expanded=False):
            st.markdown(
                """
            <div class="neo-card yellow" style="text-align: left; padding: 15px; margin-bottom: 20px;">
                <div class="neo-metric-label" style="color:#664400 !important;">🏆 TOP 3 VIRAL WINNERS</div>
                <ul style="list-style: none; padding: 0; margin-top: 10px;">
            """,
                unsafe_allow_html=True,
            )

            for hp in strategy["hooking_points"]:
                score = hp.get("viral_score", 0)
                st.markdown(
                    f"""
                <li style="margin-bottom: 12px; border-bottom: 1px dashed rgba(0,0,0,0.1); padding-bottom: 8px;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
                        <span style="font-weight: 800; font-size: 1rem; color: #222;">[{hp.get("type", "General")}]</span>
                        <span style="background:black; color:white; padding: 2px 8px; border-radius: 0; font-weight: 700; font-size: 0.8rem;">Viral Score: {score}</span>
                    </div>
                    <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 4px;">"{hp.get("hook")}"</div>
                    <div style="font-size: 0.85rem; color: #555; font-style: italic;">└ {hp.get("explanation")}</div>
                </li>
                """,
                    unsafe_allow_html=True,
                )

            st.markdown("</ul></div>", unsafe_allow_html=True)


def render_youtube_tab() -> None:
    """YouTube 탭"""
    st.markdown("### 📺 YouTube 트렌드 분석")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    search_query = st.text_input("검색어", value=product.get("name", ""))
    max_results = st.slider("검색 결과 수", 1, 10, 3)

    if st.button("🔍 검색", use_container_width=True):
        st.info("YouTube 검색 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def render_naver_tab() -> None:
    """네이버 탭"""
    st.markdown("### 🛒 네이버 쇼핑 분석")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    search_query = st.text_input(
        "검색어", value=product.get("name", ""), key="naver_search"
    )
    max_results = st.slider("검색 결과 수", 5, 30, 10, key="naver_max")

    if st.button("🔍 검색", use_container_width=True, key="naver_btn"):
        st.info("네이버 쇼핑 검색 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def render_analysis_tab() -> None:
    """분석 탭"""
    st.markdown("### 📊 마케팅 분석")

    if not SessionManager.has_collected_data():
        st.warning("먼저 데이터를 수집해주세요.")
        return

    if st.button("🤖 AI 분석 실행", use_container_width=True):
        st.info("AI 분석 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def render_thumbnail_tab() -> None:
    """썸네일 탭"""
    st.markdown("### 🖼️ AI 썸네일 생성")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    hook_text = st.text_input(
        "훅 텍스트", value=f"{product.get('name', '')} 지금 바로!"
    )
    style = st.selectbox("스타일", ["드라마틱", "미니멀", "모던", "레트로"])

    if st.button("🎨 썸네일 생성", use_container_width=True):
        st.info("썸네일 생성 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def render_video_tab() -> None:
    """비디오 탭"""
    st.markdown("### 🎬 AI 비디오 생성")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    duration = st.selectbox("비디오 길이", [8, 15, 30], index=0)
    resolution = st.selectbox("해상도", ["720p", "1080p"], index=0)

    if st.button("🎬 비디오 생성", use_container_width=True):
        st.info("비디오 생성 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def render_report_tab() -> None:
    """리포트 탭"""
    st.markdown("### 📄 마케팅 리포트")

    if not SessionManager.has_strategy():
        st.warning("먼저 마케팅 분석을 실행해주세요.")
        return

    if st.button("📊 리포트 생성", use_container_width=True):
        st.info("리포트 생성 기능은 서비스 레이어와 연결 후 활성화됩니다.")


def main() -> None:
    """메인 애플리케이션"""
    log_app_start()

    # 페이지 설정
    setup_page()

    # 환경 설정
    setup_environment()

    # 세션 상태 초기화
    SessionManager.init_session_state()

    # 스타일 주입
    inject_neobrutalism_css()

    # 사이드바
    render_sidebar()

    # 헤더
    render_header()

    # 메트릭
    render_metrics()

    st.markdown("---")

    # 탭
    render_tabs()

    # 푸터
    render_footer()


if __name__ == "__main__":
    main()
