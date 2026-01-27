"""
Social Media Post Tab
SNS 채널별 포스팅 문구 생성 및 관리
"""
import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.utils.logger import log_section, log_success


def render_social_tab() -> None:
    st.markdown("### 📱 SNS 포스팅 생성")
    st.caption("X-Algorithm 인사이트를 바탕으로 각 채널에 최적화된 마케팅 문구를 생성합니다.")

    product = SessionManager.get_selected_product()
    if not product:
        st.error("??? ??????.")
        return
    strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY)

    if not product or not strategy:
        st.warning("제품 선택 및 분석(전략 수립)이 완료된 후 사용 가능합니다.")
        return

    st.info(f"선택된 제품: **{getattr(product, 'name', 'N/A')}**")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("#### ⚙️ 생성 설정")
        platforms = st.multiselect(
            "대상 플랫폼",
            ["Instagram", "Twitter(X)", "Blog"],
            default=["Instagram", "Twitter(X)", "Blog"]
        )

        if st.button("🚀 포스팅 생성", width="stretch", type="primary"):
            log_section("SNS 포스팅 생성")
            _generate_social_posts(platforms)

    with col2:
        posts = SessionManager.get("social_posts")
        if posts:
            _render_posts(posts)
        else:
            st.info("왼쪽 버튼을 눌러 포스팅을 생성하세요.")

def _generate_social_posts(platforms: list[str]) -> None:
    services = get_services()
    product = SessionManager.get_selected_product()
    if not product:
        st.error("??? ??????.")
        return
    strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY)
    collected_data = SessionManager.get("collected_data")

    # top_insights 확보
    top_insights = []
    if hasattr(collected_data, "top_insights"):
        top_insights = collected_data.top_insights
    elif isinstance(collected_data, dict):
        top_insights = collected_data.get("top_insights", [])

    with st.spinner("AI가 채널별 맞춤형 문구를 작성 중입니다..."):
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 딕셔너리 변환 (필요 시)
            if hasattr(product, "model_dump"):
                p_dict = product.model_dump()
            elif isinstance(product, dict):
                p_dict = product
            else:
                p_dict = product.__dict__

            result = loop.run_until_complete(
                services.social_media_service.generate_posts(
                    product=p_dict,
                    strategy=strategy,
                    top_insights=top_insights,
                    platforms=[p.lower() for p in platforms]
                )
            )
            loop.close()

            SessionManager.set("social_posts", result)
            log_success("SNS 포스팅 생성 완료")
            st.rerun()
        except Exception as e:
            st.error(f"생성 중 오류 발생: {e}")

def _render_posts(posts: dict) -> None:
    st.markdown("#### 🎁 생성된 포스팅")

    tab_inst, tab_twit, tab_blog = st.tabs(["📸 Instagram", "🐦 Twitter(X)", "📝 Blog"])

    with tab_inst:
        inst = posts.get("instagram", {})
        if inst:
            st.markdown(f'<div style="border: 2px solid black; padding: 15px; background: #fdf2f8; box-shadow: 4px 4px 0px 0px #000;">{inst.get("caption", "")}</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="color: blue; margin-top: 10px;">{" ".join(inst.get("hashtags", []))}</p>', unsafe_allow_html=True)
            if st.button("📋 복사 (Instagram)", key="copy_inst"):
                st.toast("클립보드 복사 기능은 브라우저 보안 정책에 따라 지원되지 않을 수 있습니다. 텍스트를 직접 드래그하여 복사하세요.")
        else:
            st.caption("데이터 없음")

    with tab_twit:
        twit = posts.get("twitter", {})
        if twit:
            st.markdown(f'<div style="border: 2px solid black; padding: 15px; background: #f0f9ff; box-shadow: 4px 4px 0px 0px #000;">{twit.get("content", "")}</div>', unsafe_allow_html=True)
        else:
            st.caption("데이터 없음")

    with tab_blog:
        blog = posts.get("blog", {})
        if blog:
            st.markdown(f"**제목: {blog.get('title', '')}**")
            st.markdown(f'<div style="border: 2px solid black; padding: 15px; background: white; box-shadow: 4px 4px 0px 0px #000;">{blog.get("content", "")}</div>', unsafe_allow_html=True)
        else:
            st.caption("데이터 없음")
