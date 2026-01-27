"""
Report Tab Module
성과 요약, 콘텐츠 갤러리, 내보내기 기능을 제공합니다.
"""

import os
import re
import tempfile

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.config.settings import get_settings
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.utils.media import render_video
from genesis_ai.utils.logger import log_error


def render_report_tab() -> None:
    """리포트 탭 렌더링"""
    st.markdown("### 📄 마케팅 성과 리포트")

    # 히스토리는 항상 조회 가능
    _render_project_history()
    st.divider()

    if not SessionManager.has_strategy():
        st.warning("분석 결과가 없습니다. 파이프라인을 실행하거나 히스토리에서 과거 프로젝트를 불러오세요.")
        return

    # 1. 성과 요약 대시보드
    _render_dashboard()

    # 2. 콘텐츠 갤러리
    st.divider()
    _render_content_gallery()

    # 4. 내보내기 (Export)
    st.divider()
    _render_export_section()


def _render_dashboard() -> None:
    """성과 요약 대시보드"""
    collected_data = SessionManager.get("collected_data") or {}
    if hasattr(collected_data, "model_dump"):
        collected_data = collected_data.model_dump()

    strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY) or {}
    product = SessionManager.get_selected_product()
    product_name = getattr(product, "name", "제품")

    st.markdown(f"#### 📊 {product_name} 분석 대시보드")

    # 상단 메트릭 카드 (Grid Layout)
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)

    youtube_data = collected_data.get("youtube_data", {})
    video_count = len(youtube_data.get("videos", []))

    naver_data = collected_data.get("naver_data", {})
    product_count = len(naver_data.get("items", []))

    keywords = strategy.get("keywords", [])
    persona = strategy.get("target_audience", {}).get("age_group", "N/A")

    from genesis_ai.presentation.styles.neobrutalism import render_metric_card

    with m_col1:
        st.markdown(
            render_metric_card("📺", f"{video_count}", "분석된 영상", "blue"),
            unsafe_allow_html=True,
        )
    with m_col2:
        st.markdown(
            render_metric_card("🛍️", f"{product_count}", "네이버 쇼핑", "green"),
            unsafe_allow_html=True,
        )
    with m_col3:
        st.markdown(
            render_metric_card("🔑", f"{len(keywords)}", "핵심 키워드", "yellow"),
            unsafe_allow_html=True,
        )
    with m_col4:
        st.markdown(
            render_metric_card("🎯", persona, "타겟 연령", "pink"),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # 핵심 전략 요약 & 로그
    c1, c2 = st.columns([2, 1])

    with c1:
        st.markdown("##### 💡 핵심 전략 인사이트")
        if "summary" in strategy:
            st.info(f"{strategy['summary']}")
        else:
            st.info("아직 전략이 수립되지 않았습니다. 분석 탭에서 분석을 진행해주세요.")

    with c2:
        logs = SessionManager.get("pipeline_execution_logs")
        if logs:
            with st.expander("📜 파이프라인 로그", expanded=False):
                log_lines = [log.get("raw", str(log)) for log in logs]
                st.code("\n".join(log_lines), language="text")
        else:
            st.caption("실행 로그 없음")

    # X-Algorithm 인사이트 섹션 추가
    top_insights = collected_data.get("top_insights", [])
    if top_insights:
        st.markdown("---")
        st.markdown("##### 🧠 X-Algorithm 핵심 인사이트 (High Engagement Predictions)")
        st.caption("AI 알고리즘이 분석한 고가치 잠재 고객의 목소리와 구매 결정 요인")

        cols = st.columns(len(top_insights) if len(top_insights) > 0 else 1)
        for idx, insight in enumerate(top_insights):
            with cols[idx]:
                score = insight.get("score", 0)
                content = insight.get("content", "")
                features = insight.get("features", {})
                color = "#ff3333" if score > 0.8 else "#ffcc00"

                st.markdown(
                    f"""
                    <div style="border: 3px solid black; padding: 15px; background: white; box-shadow: 5px 5px 0px 0px #000; height: 100%;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span style="background: {color}; color: black; padding: 2px 8px; font-weight: bold; border: 2px solid black;">
                                SCORE: {score:.2f}
                            </span>
                        </div>
                        <p style="font-size: 0.9em; font-weight: 500; min-height: 80px; color: black;">"{content}"</p>
                        <div style="font-size: 0.8em; color: #333;">
                            <b>📌 Keywords:</b> {", ".join(features.get("keywords", [])[:3])}<br>
                            <b>💰 Intent:</b> {features.get("purchase_intent", 0):.1f} |
                            <b>💬 Viral:</b> {features.get("reply_inducing", 0):.1f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_content_gallery() -> None:
    """콘텐츠 갤러리"""
    import os
    import platform
    import subprocess

    st.markdown("#### 🖼️ Content Gallery")

    # 현재 세션에서 생성된 콘텐츠 가져오기
    thumbnail_data = SessionManager.get(SessionManager.GENERATED_THUMBNAIL)
    video_url = SessionManager.get(SessionManager.GENERATED_VIDEO)
    ab_thumbnails = SessionManager.get("ab_test_thumbnails")

    if not (thumbnail_data or video_url or ab_thumbnails):
        st.info(
            "생성된 콘텐츠가 없습니다. 파이프라인이나 각 탭에서 콘텐츠를 생성해주세요."
        )
        return

    tab1, tab2 = st.tabs(["최신 결과물", "A/B 테스트 세트"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            if thumbnail_data:
                st.image(
                    thumbnail_data, caption="최종 썸네일", width="stretch"
                )
            else:
                st.caption("생성된 썸네일 없음")

        with c2:
            if video_url:
                # 비디오 렌더링 (로컬/URL 처리)
                if os.path.exists(video_url):
                    try:
                        with open(video_url, "rb") as f:
                            video_bytes = f.read()
                        render_video(video_bytes)
                    except Exception as e:
                        st.error(f"비디오 재생 오류: {e}")

                    st.caption(f"📍 저장 위치: `{video_url}`")
                    if st.button("📂 폴더 열기", key="open_gallery_video"):
                        folder_path = os.path.dirname(os.path.abspath(video_url))
                        if platform.system() == "Windows":
                            os.startfile(folder_path)
                        elif platform.system() == "Darwin":
                            subprocess.Popen(["open", folder_path])
                        else:
                            subprocess.Popen(["xdg-open", folder_path])
                else:
                    render_video(video_url)
                    st.caption("최종 생성 비디오")
            else:
                st.caption("생성된 비디오 없음")

    with tab2:
        if ab_thumbnails:
            cols = st.columns(3)
            for idx, item in enumerate(ab_thumbnails):
                with cols[idx % 3]:
                    if item.get("image"):
                        st.image(
                            item["image"], caption=f"Style: {item.get('style', 'N/A')}"
                        )
        else:
            st.info("생성된 A/B 테스트 썸네일 세트가 없습니다.")


def _render_project_history() -> None:
    """분석 프로젝트 히스토리 조회 및 복원"""
    with st.expander("🗄️ 프로젝트 히스토리 (X-Algorithm History)", expanded=False):
        try:
            services = get_services()
            history_service = services.history_service
            items = history_service.get_history_list()

            if not items:
                st.info("저장된 히스토리가 없습니다.")
                return

            st.caption("과거 분석 결과를 불러와서 대시보드와 리포트를 즉시 업데이트할 수 있습니다.")

            # 테이블 헤더
            h_col1, h_col2, h_col3, h_col4 = st.columns([2, 2, 1, 1])
            with h_col1:
                st.markdown("**프로젝트**")
            with h_col2:
                st.markdown("**실행 일시**")
            with h_col3:
                st.markdown("**인사이트**")
            with h_col4:
                st.markdown("**작업**")

            for item in items:
                st.divider()
                c1, c2, c3, c4 = st.columns([2, 2, 1, 1])

                with c1:
                    status_emoji = "✅" if item["success"] else "❌"
                    st.markdown(f"{status_emoji} **{item['product_name']}**")

                with c2:
                    st.caption(item["executed_at"])

                with c3:
                    st.markdown(f"`{item['top_insight_count']}개`")

                with c4:
                    if st.button("📂 열기", key=f"restore_{item['id']}", width="stretch"):
                        _restore_history(item["id"])

                    if st.button("🗑️", key=f"del_{item['id']}", width="stretch"):
                        if history_service.delete_history(item["id"]):
                            st.toast("히스토리가 삭제되었습니다.")
                            st.rerun()

        except Exception as e:
            st.error(f"히스토리 로드 실패: {e}")


def _restore_history(history_id: str):
    """과거 분석 결과를 세션으로 복원"""
    try:
        services = get_services()
        result = services.history_service.load_history(history_id)

        if not result:
            st.error("결과를 불러올 수 없습니다.")
            return

        # SessionManager를 통해 상태 복원
        SessionManager.set(SessionManager.PIPELINE_RESULT, result)
        SessionManager.set(SessionManager.COLLECTED_DATA, result.collected_data)
        SessionManager.set(SessionManager.PIPELINE_STRATEGY, result.strategy)

        # 제품 정보도 복원 시도 (있는 경우)
        if result.product_name:
            from genesis_ai.config.products import get_product_by_name
            product = get_product_by_name(result.product_name)
            if product:
                SessionManager.set(SessionManager.SELECTED_PRODUCT, product)

        # 미디어 정보 복원 (Bytes는 없으므로 Path/URL 위주)
        if result.generated_content:
            SessionManager.set(SessionManager.GENERATED_THUMBNAIL_URL, result.generated_content.thumbnail_url)
            SessionManager.set(SessionManager.GENERATED_VIDEO_URL, result.generated_content.video_url)
            SessionManager.set(SessionManager.GENERATED_VIDEO, result.generated_content.video_url or result.generated_content.video_path)

        st.success(f"'{result.product_name}' 프로젝트가 성공적으로 복원되었습니다.")
        st.rerun()

    except Exception as e:
        st.error(f"복원 중 오류 발생: {e}")


def _render_export_section() -> None:
    """내보내기 섹션 (PDF/Notion)"""
    st.markdown("#### 📤 Export")

    c1, c2 = st.columns(2)

    # PDF
    with c1:
        st.markdown("##### PDF 리포트")
        if st.button("📄 PDF 생성 및 다운로드", width="stretch"):
            _handle_pdf_export()

    # Notion
    with c2:
        st.markdown("##### Notion 내보내기")
        with st.popover("Notion 설정"):
            settings = get_settings()
            secrets_key = ""
            try:
                secrets_key = st.secrets.get("NOTION_API_KEY", "")
            except Exception:
                secrets_key = ""

            env_key = settings.notion_api_key or secrets_key
            key_source = "환경 변수" if settings.has_notion_api_key() else ""
            if not key_source and secrets_key:
                key_source = "Streamlit secrets"

            if env_key:
                st.success(f"Notion API Key 설정됨 ({key_source})")
                use_override = st.checkbox(
                    "키를 직접 입력",
                    value=False,
                    key="notion_key_override",
                )
            else:
                st.warning("Notion API Key가 설정되지 않았습니다. 아래에 입력해주세요.")
                use_override = True

            notion_key = ""
            if use_override:
                notion_key = st.text_input(
                    "Notion API Key",
                    type="password",
                    key="notion_key_input",
                )
            else:
                notion_key = env_key

            page_id = st.text_input("Parent Page ID", key="notion_page_id")
            normalized_page_id = _normalize_notion_page_id(page_id)
            page_id_valid = bool(normalized_page_id)
            if page_id and not page_id_valid:
                st.caption("올바른 Notion 페이지 ID 또는 URL을 입력해주세요.")

            if st.button(
                "전송",
                disabled=not (notion_key and page_id_valid),
            ):
                _handle_notion_export(notion_key, normalized_page_id)


def _handle_pdf_export():
    try:
        services = get_services()
        collected_data = SessionManager.get("collected_data")
        if hasattr(collected_data, "model_dump"):
            collected_data = collected_data.model_dump()

        strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY)
        product = SessionManager.get_selected_product()

        export_data = {
            "product": product,
            "metrics": collected_data,
            "analysis": strategy,
        }

        with st.spinner("PDF 리포트 생성 중..."):
            export_service = services.export_service
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                pdf_path = export_service.export_pdf(export_data, tmp.name)

                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()

                st.download_button(
                    label="⬇️ 파일 다운로드",
                    data=pdf_bytes,
                    file_name=f"{getattr(product, 'name', 'report')}_report.pdf",
                    mime="application/pdf",
                    width="stretch",
                )
                os.unlink(pdf_path)
    except Exception as e:
        st.error(f"PDF 생성 실패: {e}")
        log_error(f"PDF Export Error: {e}")


def _handle_notion_export(api_key: str, page_id: str):
    try:
        from genesis_ai.infrastructure.clients.notion_client import NotionClient

        with st.spinner("Notion 페이지 생성 중..."):
            collected_data = SessionManager.get("collected_data")
            if hasattr(collected_data, "model_dump"):
                collected_data = collected_data.model_dump()

            strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY)
            product = SessionManager.get_selected_product()
            if not product:
                st.error("??? ??????.")
                return

            if hasattr(product, "model_dump"):
                product_dict = product.model_dump()
            elif isinstance(product, dict):
                product_dict = product
            else:
                product_dict = product.__dict__

            export_data = {
                "product": product_dict,
                "metrics": collected_data,
                "analysis": strategy,
            }

            client = NotionClient(api_key=api_key)
            url = client.export(export_data, page_id)
            st.success(f"Notion 페이지 생성 완료! [보러가기]({url})")

    except Exception as e:
        st.error(f"Notion 전송 실패: {e}")
        log_error(f"Notion Export Error: {e}")


def _normalize_notion_page_id(value: str) -> str:
    """Notion 페이지 ID를 정규화하고 검증합니다."""
    if not value:
        return ""

    text = value.strip()
    # URL에서 ID 추출
    match = re.search(
        r"([0-9a-fA-F]{32})|([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
        text,
    )
    if not match:
        return ""

    raw_id = match.group(0)
    normalized = raw_id.replace("-", "")
    if len(normalized) != 32:
        return ""

    return normalized
