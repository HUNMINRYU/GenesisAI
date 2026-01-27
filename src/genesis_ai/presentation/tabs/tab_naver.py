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


def render_naver_tab() -> None:
    """네이버 탭"""
    st.markdown("### 🛒 네이버 쇼핑 분석")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    search_query = st.text_input(
        "검색어", value=getattr(product, "name", ""), key="naver_search"
    )
    max_results = st.slider("검색 결과 수", 5, 30, 10, key="naver_max")

    if st.button("🔍 검색", width="stretch", key="naver_btn"):
        log_section("네이버 쇼핑 분석")
        log_user_action("네이버 검색", f"쿼리='{search_query}', 최대={max_results}")
        perform_naver_search(search_query, max_results)


@safe_action(context="네이버 쇼핑 검색")
def perform_naver_search(query: str, max_results: int) -> None:
    """네이버 검색 실행 로직"""
    with st.spinner("네이버 쇼핑 데이터 수집 중..."):
        services = get_services()
        products = services.naver_service.search_products(
            query=query, max_results=max_results
        )

        SessionManager.set_collected_section("naver_data", {"items": products})

        log_data("네이버 상품", len(products), "API")
        log_success(f"네이버 쇼핑 데이터 수집 완료 ({len(products)}개)")

        # Display Logic
        st.success(f"{len(products)}개의 상품을 찾았습니다.")
        for prod in products:
            title = prod.get("title", "No Title")
            price = prod.get("price", 0)
            mall = prod.get("mall", "N/A")

            with st.expander(f"🛍️ {title}", expanded=False):
                c1, c2 = st.columns([1, 2])
                with c1:
                    if "image" in prod:
                        st.image(prod["image"], width="stretch")
                with c2:
                    st.markdown(f"**가격**: {price:,}원")
                    st.caption(f"판매처: {mall}")
                    st.caption(
                        f"카테고리: {prod.get('category1', '')} > {prod.get('category2', '')}"
                    )
                    if "link" in prod:
                        st.markdown(f"[🔗 상품 보러가기]({prod['link']})")
