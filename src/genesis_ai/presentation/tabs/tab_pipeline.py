from datetime import datetime

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.core.models import PipelineConfig
from genesis_ai.presentation.components.log_viewer import render_inline_terminal
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.utils.media import render_video
from genesis_ai.utils.file_store import save_thumbnail_bytes, save_video_bytes
from genesis_ai.utils.logger import (
    get_logger,
    log_error,
    log_section,
    log_user_action,
)

# 파이프라인 실행 로그 세션 키
PIPELINE_LOG_KEY = "pipeline_execution_logs"


def render_pipeline_tab() -> None:
    """파이프라인 탭"""
    st.markdown("### 🚀 자동화 파이프라인")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    st.info(f"선택된 제품: **{getattr(product, 'name', 'N/A')}**")

    # 설정 UI
    with st.expander("⚙️ 파이프라인 설정", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            youtube_count = st.slider("YouTube 검색 수", 1, 10, 3)
            include_comments = st.checkbox("댓글 분석 포함", value=True)
        with c2:
            naver_count = st.slider("네이버 쇼핑 검색 수", 5, 30, 10)
            generate_social = st.checkbox("SNS 포스팅 생성", value=True)
            generate_video = st.checkbox("비디오 생성", value=True)
            generate_thumbnails = st.checkbox("썸네일 3종 생성", value=True)

    if st.button("🚀 파이프라인 실행", width="stretch", type="primary"):
        # 전역 로그가 수집하므로 여기서는 별도 처리 불필요
        # 단, 새로운 실행 시 로그를 구분하고 싶다면 전역 로그에 구분선 추가 가능
        log_section("파이프라인 실행 시작")
        log_user_action(
            "파이프라인 실행 버튼 클릭",
            f"제품={getattr(product, 'name', 'N/A')}, YT={youtube_count}, NV={naver_count}",
        )

        _execute_pipeline(
            product=product.model_dump()
            if hasattr(product, "model_dump")
            else product.__dict__,
            youtube_count=youtube_count,
            naver_count=naver_count,
            include_comments=include_comments,
            generate_social=generate_social,
            generate_video=generate_video,
            generate_thumbnails=generate_thumbnails,
        )

    # 세션에 결과가 있으면 항상 표시 (st.rerun() 후에도 유지)
    elif SessionManager.get(SessionManager.PIPELINE_EXECUTED):
        _render_cached_results()


def _execute_pipeline(
    product: dict,
    youtube_count: int,
    naver_count: int,
    include_comments: bool,
    generate_social: bool,
    generate_video: bool,
    generate_thumbnails: bool,
) -> None:
    """파이프라인 실행 로직"""
    # 터미널 로그 영역
    st.markdown("#### 📟 실행 로그")
    log_placeholder = st.empty()

    # 파이프라인 로그 초기화
    pipeline_logs: list[dict[str, str]] = []
    SessionManager.set(PIPELINE_LOG_KEY, pipeline_logs)

    # 초기 터미널 렌더링
    render_inline_terminal(log_placeholder, pipeline_logs)

    try:
        services = get_services()
        pipeline_service = services.pipeline_service

        config = PipelineConfig(
            youtube_count=youtube_count,
            naver_count=naver_count,
            include_comments=include_comments,
            generate_social=generate_social,
            generate_video=generate_video,
            generate_thumbnail=generate_thumbnails,
            generate_multi_thumbnails=generate_thumbnails,
            thumbnail_count=3 if generate_thumbnails else 1,
            upload_to_gcs=True,
        )
        SessionManager.reset_pipeline_state()
        SessionManager.set_pipeline_config(config)
        progress = SessionManager.get_pipeline_progress()
        progress.configure_steps(config)
        SessionManager.set(SessionManager.PIPELINE_PROGRESS, progress)

        def progress_callback(progress):
            nonlocal pipeline_logs

            # PipelineProgress 객체를 받아 처리
            step_name = (
                progress.current_step.name
                if hasattr(progress.current_step, "name")
                else str(progress.current_step)
            )

            message = f"[{step_name}] {progress.message}"

            # 터미널 로그에 추가
            log_entry = {
                "emoji": "📌",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": message,
                "raw": f"📌 [{datetime.now().strftime('%H:%M:%S')}] INFO - {message}",
            }
            pipeline_logs.append(log_entry)
            SessionManager.set(PIPELINE_LOG_KEY, pipeline_logs)

            # 터미널 UI 즉시 업데이트
            render_inline_terminal(log_placeholder, pipeline_logs)

            # 전역 로거에도 기록
            get_logger().info(f"[PROGRESS] {message}")

        result = pipeline_service.execute(
            product=product, config=config, progress_callback=progress_callback
        )

        if result.success:
            # 완료 로그 추가
            pipeline_logs.append({
                "emoji": "✅",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": "파이프라인 실행 완료!",
                "raw": f"✅ [{datetime.now().strftime('%H:%M:%S')}] INFO - 완료!",
            })
            render_inline_terminal(log_placeholder, pipeline_logs)

            st.success("모든 작업이 성공적으로 완료되었습니다!")

            # 결과 저장
            SessionManager.set_pipeline_result(result)

            # 저장 경로 로그 추가
            if hasattr(result, "executed_at"):
                pipeline_logs.append({
                    "emoji": "💾",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "level": "INFO",
                    "message": "분석 결과가 영구 저장되었습니다. (리포트 탭에서 확인 가능)",
                    "raw": f"💾 [{datetime.now().strftime('%H:%M:%S')}] INFO - 결과 저장 완료",
                })
                render_inline_terminal(log_placeholder, pipeline_logs)

            # 결과 렌더링
            try:
                render_pipeline_results(result, show_balloons=True)
            except Exception as render_error:
                import traceback

                log_error(f"결과 렌더링 실패: {render_error}")
                st.error("결과 렌더링 중 오류가 발생했습니다.")
                st.code(traceback.format_exc(), language="text")

        else:
            # 실패 로그 추가
            pipeline_logs.append({
                "emoji": "❌",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": f"실행 실패: {result.error_message}",
                "raw": f"❌ [{datetime.now().strftime('%H:%M:%S')}] ERROR - 실패",
            })
            render_inline_terminal(log_placeholder, pipeline_logs)

            st.error(f"오류가 발생했습니다: {result.error_message}")
            # 부분 결과가 있으면 저장/표시
            SessionManager.set_pipeline_result(result)
            if result.collected_data or result.strategy or result.generated_content:
                st.warning("일부 단계만 완료되었습니다. 가능한 결과를 표시합니다.")
                render_pipeline_results(result)

    except Exception as e:
        # 예외 로그 추가
        pipeline_logs.append({
            "emoji": "🚨",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": "CRITICAL",
            "message": f"치명적 오류: {e}",
            "raw": f"🚨 [{datetime.now().strftime('%H:%M:%S')}] CRITICAL - {e}",
        })
        render_inline_terminal(log_placeholder, pipeline_logs)

        log_error(f"파이프라인 실행 중 예외: {e}")
        st.error(f"실행 중 오류 발생: {e}")


def _render_cached_results() -> None:
    """세션에서 캐시된 결과 렌더링 (st.rerun 후에도 유지)"""
    result = SessionManager.get(SessionManager.PIPELINE_RESULT)
    if result:
        render_pipeline_results(result, show_balloons=False)
        return

    # Fallback: 개별 세션 변수 렌더링 (구버전 호환용)
    import os
    import platform
    import subprocess

    st.divider()
    st.markdown("### 🎁 생성 결과물")

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### 🖼️ 썸네일")
        multi_thumbnails = SessionManager.get(SessionManager.MULTI_THUMBNAILS)
        selected_index = st.session_state.get("pipeline_thumbnail_selected_index", 0)

        if multi_thumbnails:
            thumb_cols = st.columns(3)
            for idx, item in enumerate(multi_thumbnails[:3]):
                with thumb_cols[idx]:
                    image_bytes = item.get("image") or item.get("image_bytes")
                    style_label = item.get(
                        "style_name", item.get("style", f"Style {idx + 1}")
                    )
                    if image_bytes:
                        st.image(image_bytes, caption=style_label)
                        if st.button(
                            f"선택 {idx + 1}",
                            key=f"cached_thumb_select_{idx}",
                            width="stretch",
                        ):
                            st.session_state["pipeline_thumbnail_selected_index"] = idx
                            st.rerun()

            # 선택된 썸네일 크게 표시
            selected_item = multi_thumbnails[
                min(selected_index, len(multi_thumbnails) - 1)
            ]
            selected_bytes = selected_item.get("image") or selected_item.get(
                "image_bytes"
            )
            if selected_bytes:
                SessionManager.set(SessionManager.GENERATED_THUMBNAIL, selected_bytes)
                st.markdown("##### 선택된 썸네일")
                st.image(
                    selected_bytes,
                    caption=selected_item.get("style_name", "Selected Thumbnail"),
                )
        elif SessionManager.get(SessionManager.GENERATED_THUMBNAIL):
            st.image(
                SessionManager.get(SessionManager.GENERATED_THUMBNAIL),
                caption="Generated Thumbnail",
            )
        else:
            st.info("생성된 썸네일이 없습니다.")

    with r_col2:
        st.markdown("#### 🎬 비디오")
        video_bytes = SessionManager.get(SessionManager.VIDEO_BYTES)
        video_url = SessionManager.get(SessionManager.GENERATED_VIDEO_URL)

        if video_bytes:
            render_video(video_bytes)
            if video_url:
                st.caption(f"☁️ 버킷 저장: `{video_url}`")
        elif video_url:
            if os.path.exists(video_url):
                try:
                    with open(video_url, "rb") as v_file:
                        vb = v_file.read()
                    render_video(vb)
                except Exception as e:
                    st.error(f"비디오 로드 실패: {e}")
                st.caption(f"📍 저장 위치: `{video_url}`")
                if st.button("📂 폴더 열기", key="cached_open_video_folder"):
                    folder_path = os.path.dirname(os.path.abspath(video_url))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", folder_path])
                    else:
                        subprocess.Popen(["xdg-open", folder_path])
            else:
                render_video(video_url)
                st.markdown(f"[🔗 비디오 링크]({video_url})")
        else:
            st.info("생성된 비디오가 없습니다.")


def render_pipeline_results(result, show_balloons: bool = False) -> None:
    """파이프라인 실행 결과 렌더링"""
    import os
    import platform
    import subprocess

    # 썸네일/비디오 세션 저장 및 결과 표시
    st.divider()
    st.markdown("### 🎁 생성 결과물")

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### 🖼️ 썸네일")
        selected_index = st.session_state.get("pipeline_thumbnail_selected_index", 0)

        if result.generated_content.multi_thumbnails:
            thumb_cols = st.columns(3)
            for idx, item in enumerate(result.generated_content.multi_thumbnails[:3]):
                with thumb_cols[idx]:
                    image_bytes = item.get("image") or item.get("image_bytes")
                    style_label = item.get("style_name", item.get("style", f"Style {idx + 1}"))
                    if image_bytes:
                        st.image(image_bytes, caption=style_label)
                        if st.button(
                            f"선택 {idx + 1}",
                            key=f"thumb_select_{idx}",
                            width="stretch",
                        ):
                            st.session_state["pipeline_thumbnail_selected_index"] = idx
                            st.rerun()

            selected_item = result.generated_content.multi_thumbnails[
                min(selected_index, len(result.generated_content.multi_thumbnails) - 1)
            ]
            selected_bytes = selected_item.get("image") or selected_item.get("image_bytes")
            if selected_bytes:
                SessionManager.set(SessionManager.GENERATED_THUMBNAIL, selected_bytes)
                st.image(
                    selected_bytes,
                    caption=selected_item.get("style_name", "Selected Thumbnail"),
                )
        elif result.generated_content.thumbnail_data:
            SessionManager.set(
                SessionManager.GENERATED_THUMBNAIL,
                result.generated_content.thumbnail_data,
            )
            st.image(
                result.generated_content.thumbnail_data,
                caption="Generated Thumbnail",
            )
            if SessionManager.get(SessionManager.GENERATED_THUMBNAIL_URL):
                st.caption(
                    f"☁️ 버킷 저장: `{SessionManager.get(SessionManager.GENERATED_THUMBNAIL_URL)}`"
                )
            if st.button("💾 로컬로 저장 (썸네일)", key="save_thumb_local"):
                path = save_thumbnail_bytes(result.generated_content.thumbnail_data)
                SessionManager.set(SessionManager.GENERATED_THUMBNAIL_PATH, path)
                st.caption(f"📍 저장 위치: `{path}`")
                st.download_button(
                    "⬇️ 썸네일 다운로드",
                    data=result.generated_content.thumbnail_data,
                    file_name=path.split("\\")[-1],
                    mime="image/png",
                )
            # 썸네일 경로 (메모리상의 데이터라 경로가 없을 수 있음, 저장 후 경로 표시 추천하지만 현재는 데이터만 있음)
            # 만약 파일로 저장된 경로가 있다면 표시 (Result 객체 구조에 따라 다름)
        else:
            st.info("생성된 썸네일이 없습니다.")

    with r_col2:
        st.markdown("#### 🎬 비디오")
        video_url = result.generated_content.video_url
        video_bytes = result.generated_content.video_bytes
        if video_bytes:
            SessionManager.set(
                SessionManager.GENERATED_VIDEO,
                "bytes",
            )
            render_video(video_bytes)
            if SessionManager.get(SessionManager.GENERATED_VIDEO_URL):
                st.caption(
                    f"☁️ 버킷 저장: `{SessionManager.get(SessionManager.GENERATED_VIDEO_URL)}`"
                )
            if st.button("💾 로컬로 저장 (비디오)", key="save_video_local"):
                path = save_video_bytes(video_bytes)
                SessionManager.set(SessionManager.GENERATED_VIDEO_PATH, path)
                st.caption(f"📍 저장 위치: `{path}`")
                st.download_button(
                    "⬇️ 비디오 다운로드",
                    data=video_bytes,
                    file_name=path.split("\\")[-1],
                    mime="video/mp4",
                )
        elif video_url:
            SessionManager.set(
                SessionManager.GENERATED_VIDEO,
                video_url,
            )

            # 로컬 파일 처리
            if os.path.exists(video_url):
                # 1. 화면 표시 (바이트로 읽기)
                try:
                    with open(video_url, "rb") as v_file:
                        video_bytes = v_file.read()
                    render_video(video_bytes)
                except Exception as e:
                    st.error(f"비디오 로드 실패: {e}")

                # 2. 경로 및 폴더 열기
                st.caption(f"📍 저장 위치: `{video_url}`")

                if st.button("📂 폴더 열기", key="open_video_folder"):
                    folder_path = os.path.dirname(os.path.abspath(video_url))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", folder_path])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", folder_path])
            else:
                # URL인 경우
                render_video(video_url)
                st.markdown(f"[🔗 비디오 링크]({video_url})")

        else:
            st.info("생성된 비디오가 없습니다.")

    # 전략 요약 표시
    if result.strategy:
        with st.expander("📊 마케팅 전략 요약", expanded=True):
            st.write(result.strategy.get("summary", "요약 정보 없음"))

    # X-Algorithm 인사이트 섹션
    if (
        result.collected_data
        and hasattr(result.collected_data, "top_insights")
        and result.collected_data.top_insights
    ):
        st.divider()
        st.markdown("### 🧠 X-Algorithm 핵심 인사이트")
        st.caption("AI 알고리즘이 분석한 유튜브 댓글 기반 고가치 잠재 고객의 페인포인트와 구매 의도")

        insights = result.collected_data.top_insights
        insight_cols = st.columns(len(insights))
        for idx, insight in enumerate(insights):
            with insight_cols[idx]:
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
                        <p style="font-size: 0.9em; font-weight: 500; min-height: 80px;">"{content}"</p>
                        <div style="font-size: 0.8em; color: #333;">
                            <b>📌 Keywords:</b> {", ".join(features.get("keywords", [])[:3])}<br>
                            <b>💰 Intent:</b> {features.get("purchase_intent", 0):.1f} |
                            <b>💬 Viral:</b> {features.get("reply_inducing", 0):.1f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if show_balloons:
        st.balloons()
