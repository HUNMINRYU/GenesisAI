import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.utils.error_handler import safe_action
from genesis_ai.utils.logger import (
    log_data,
    log_section,
    log_success,
    log_user_action,
)


def render_youtube_tab() -> None:
    """YouTube 탭"""
    st.markdown("### 📺 YouTube 트렌드 분석")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    search_query = st.text_input("검색어", value=getattr(product, "name", ""))
    max_results = st.slider("검색 결과 수", 1, 10, 3)

    if st.button("🔍 검색", width="stretch"):
        log_section("YouTube 분석")
        log_user_action("YouTube 검색", f"쿼리='{search_query}', 최대={max_results}")
        perform_youtube_search(search_query, max_results)


@safe_action(context="YouTube 검색")
def perform_youtube_search(query: str, max_results: int) -> None:
    """YouTube 검색 실행 및 결과 처리 (분리된 로직)"""
    with st.spinner("YouTube 데이터 수집 중..."):
        services = get_services()
        videos = services.youtube_service.search_videos(
            query=query, max_results=max_results
        )

        SessionManager.set_collected_section("youtube_data", {"videos": videos})

        # Logging
        log_data("YouTube 영상", len(videos), "API")
        log_success(f"YouTube 데이터 수집 완료 ({len(videos)}개)")

        # Display Logic
        st.success(f"{len(videos)}개의 영상을 찾았습니다.")
        for video in videos:
            with st.expander(f"📺 {video.get('title', 'No Title')}", expanded=False):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if "thumbnail" in video:
                        st.image(video["thumbnail"])
                    elif "thumbnail_url" in video:
                        st.image(video["thumbnail_url"])
                with c2:
                    view_count = video.get("view_count", 0)
                    st.write(f"조회수: {view_count:,}")
                    st.write(f"게시일: {video.get('published_at', '')}")
                    st.caption(video.get("description", "")[:100] + "...")
