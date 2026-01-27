from datetime import datetime

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.core.models import PipelineConfig, PipelineResult, GeneratedContent
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

# ?뚯씠?꾨씪???ㅽ뻾 濡쒓렇 ?몄뀡 ??
PIPELINE_LOG_KEY = "pipeline_execution_logs"


def render_pipeline_tab() -> None:
    """?뚯씠?꾨씪????""
    st.markdown("### ?? ?먮룞???뚯씠?꾨씪??)

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("?쒗뭹??癒쇱? ?좏깮?댁＜?몄슂.")
        return

    st.info(f"?좏깮???쒗뭹: **{getattr(product, 'name', 'N/A')}**")

    # ?ㅼ젙 UI
    with st.expander("?숋툘 ?뚯씠?꾨씪???ㅼ젙", expanded=True):
        c1, c2 = st.columns(2)
        with c1:
            youtube_count = st.slider("YouTube 寃????, 1, 10, 3)
            include_comments = st.checkbox("?볤? 遺꾩꽍 ?ы븿", value=True)
        with c2:
            naver_count = st.slider("?ㅼ씠踰??쇳븨 寃????, 5, 30, 10)
            generate_social = st.checkbox("SNS ?ъ뒪???앹꽦", value=True)
            generate_video = st.checkbox("鍮꾨뵒???앹꽦", value=True)
            generate_thumbnails = st.checkbox("?몃꽕??3醫??앹꽦", value=True)

    if st.button("?? ?뚯씠?꾨씪???ㅽ뻾", width="stretch", type="primary"):
        # ?꾩뿭 濡쒓렇媛 ?섏쭛?섎?濡??ш린?쒕뒗 蹂꾨룄 泥섎━ 遺덊븘??
        # ?? ?덈줈???ㅽ뻾 ??濡쒓렇瑜?援щ텇?섍퀬 ?띕떎硫??꾩뿭 濡쒓렇??援щ텇??異붽? 媛??
        log_section("?뚯씠?꾨씪???ㅽ뻾 ?쒖옉")
        log_user_action(
            "?뚯씠?꾨씪???ㅽ뻾 踰꾪듉 ?대┃",
            f"?쒗뭹={getattr(product, 'name', 'N/A')}, YT={youtube_count}, NV={naver_count}",
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

    # ?몄뀡??寃곌낵媛 ?덉쑝硫???긽 ?쒖떆 (st.rerun() ?꾩뿉???좎?)
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
    """?뚯씠?꾨씪???ㅽ뻾 濡쒖쭅"""
    # ?곕???濡쒓렇 ?곸뿭
    st.markdown("#### ?뱹 ?ㅽ뻾 濡쒓렇")
    log_placeholder = st.empty()

    # ?뚯씠?꾨씪??濡쒓렇 珥덇린??
    pipeline_logs: list[dict[str, str]] = []
    SessionManager.set(PIPELINE_LOG_KEY, pipeline_logs)
    SessionManager.set(SessionManager.PIPELINE_ERROR_LOGS, [])

    # 珥덇린 ?곕????뚮뜑留?
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

            # PipelineProgress 媛앹껜瑜?諛쏆븘 泥섎━
            step_name = (
                progress.current_step.name
                if hasattr(progress.current_step, "name")
                else str(progress.current_step)
            )

            message = f"[{step_name}] {progress.message}"

            # ?곕???濡쒓렇??異붽?
            log_entry = {
                "emoji": "?뱦",
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": message,
                "raw": f"?뱦 [{datetime.now().strftime('%H:%M:%S')}] INFO - {message}",
            }
            pipeline_logs.append(log_entry)
            SessionManager.set(PIPELINE_LOG_KEY, pipeline_logs)

            # ?곕???UI 利됱떆 ?낅뜲?댄듃
            render_inline_terminal(log_placeholder, pipeline_logs)

            # ?꾩뿭 濡쒓굅?먮룄 湲곕줉
            get_logger().info(f"[PROGRESS] {message}")

        result = pipeline_service.execute(
            product=product, config=config, progress_callback=progress_callback
        )

        if result.success:
            # ?꾨즺 濡쒓렇 異붽?
            pipeline_logs.append({
                "emoji": "??,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "INFO",
                "message": "?뚯씠?꾨씪???ㅽ뻾 ?꾨즺!",
                "raw": f"??[{datetime.now().strftime('%H:%M:%S')}] INFO - ?꾨즺!",
            })
            render_inline_terminal(log_placeholder, pipeline_logs)

            st.success("紐⑤뱺 ?묒뾽???깃났?곸쑝濡??꾨즺?섏뿀?듬땲??")

            # 寃곌낵 ???
            SessionManager.set_pipeline_result(result)

            # ???寃쎈줈 濡쒓렇 異붽?
            if hasattr(result, "executed_at"):
                pipeline_logs.append({
                    "emoji": "?뮶",
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "level": "INFO",
                    "message": "遺꾩꽍 寃곌낵媛 ?곴뎄 ??λ릺?덉뒿?덈떎. (由ы룷????뿉???뺤씤 媛??",
                    "raw": f"?뮶 [{datetime.now().strftime('%H:%M:%S')}] INFO - 寃곌낵 ????꾨즺",
                })
                render_inline_terminal(log_placeholder, pipeline_logs)

            # 寃곌낵 ?뚮뜑留?
            try:
                render_pipeline_results(result, show_balloons=True)
            except Exception as render_error:
                import traceback

                log_error(f"寃곌낵 ?뚮뜑留??ㅽ뙣: {render_error}")
                st.error("寃곌낵 ?뚮뜑留?以??ㅻ쪟媛 諛쒖깮?덉뒿?덈떎.")
                st.code(traceback.format_exc(), language="text")

        else:
            # ?ㅽ뙣 濡쒓렇 異붽?
            pipeline_logs.append({
                "emoji": "??,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "level": "ERROR",
                "message": f"?ㅽ뻾 ?ㅽ뙣: {result.error_message}",
                "raw": f"??[{datetime.now().strftime('%H:%M:%S')}] ERROR - ?ㅽ뙣",
            })
            render_inline_terminal(log_placeholder, pipeline_logs)

            st.error(f"?ㅻ쪟媛 諛쒖깮?덉뒿?덈떎: {result.error_message}")
            # 遺遺?寃곌낵媛 ?덉쑝硫?????쒖떆
            SessionManager.set_pipeline_result(result)
            if result.collected_data or result.strategy or result.generated_content:
                st.warning("?쇰? ?④퀎留??꾨즺?섏뿀?듬땲?? 媛?ν븳 寃곌낵瑜??쒖떆?⑸땲??")
                render_pipeline_results(result)

    except Exception as e:
        # ?덉쇅 濡쒓렇 異붽?
        pipeline_logs.append({
            "emoji": "?슚",
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": "CRITICAL",
            "message": f"移섎챸???ㅻ쪟: {e}",
            "raw": f"?슚 [{datetime.now().strftime('%H:%M:%S')}] CRITICAL - {e}",
        })
        render_inline_terminal(log_placeholder, pipeline_logs)

        log_error(f"?뚯씠?꾨씪???ㅽ뻾 以??덉쇅: {e}")
        st.error(f"?ㅽ뻾 以??ㅻ쪟 諛쒖깮: {e}")

        error_result = PipelineResult(
            success=False,
            product_name=product.get("name", "N/A"),
            config=SessionManager.get_pipeline_config(),
            collected_data=None,
            strategy=None,
            generated_content=GeneratedContent(),
            error_message=str(e),
        )
        SessionManager.set_pipeline_result(error_result)
        SessionManager.set(SessionManager.PIPELINE_ERROR_LOGS, pipeline_logs)


def _render_cached_results() -> None:
    """?몄뀡?먯꽌 罹먯떆??寃곌낵 ?뚮뜑留?(st.rerun ?꾩뿉???좎?)"""
    result = SessionManager.get(SessionManager.PIPELINE_RESULT)
    cached_logs = SessionManager.get(SessionManager.PIPELINE_ERROR_LOGS)
    if cached_logs:
        st.markdown("#### ?ㅽ뻾 濡쒓렇 (罹먯떆??)")
        log_placeholder = st.empty()
        render_inline_terminal(log_placeholder, cached_logs)

    if result and not result.success:
        st.error(f"?댁쟾 ?ㅽ뻾 ?ㅻ쪟: {result.error_message}")
        return

    if result:
        render_pipeline_results(result, show_balloons=False)
        return

    # Fallback: 媛쒕퀎 ?몄뀡 蹂???뚮뜑留?(援щ쾭???명솚??
    import os
    import platform
    import subprocess

    st.divider()
    st.markdown("### ?럞 ?앹꽦 寃곌낵臾?)

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### ?뼹截??몃꽕??)
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
                            f"?좏깮 {idx + 1}",
                            key=f"cached_thumb_select_{idx}",
                            width="stretch",
                        ):
                            st.session_state["pipeline_thumbnail_selected_index"] = idx
                            st.rerun()

            # ?좏깮???몃꽕???ш쾶 ?쒖떆
            selected_item = multi_thumbnails[
                min(selected_index, len(multi_thumbnails) - 1)
            ]
            selected_bytes = selected_item.get("image") or selected_item.get(
                "image_bytes"
            )
            if selected_bytes:
                SessionManager.set(SessionManager.GENERATED_THUMBNAIL, selected_bytes)
                st.markdown("##### ?좏깮???몃꽕??)
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
            st.info("?앹꽦???몃꽕?쇱씠 ?놁뒿?덈떎.")

    with r_col2:
        st.markdown("#### ?렗 鍮꾨뵒??)
        video_bytes = SessionManager.get(SessionManager.VIDEO_BYTES)
        video_url = SessionManager.get(SessionManager.GENERATED_VIDEO_URL)

        if video_bytes:
            render_video(video_bytes)
            if video_url:
                st.caption(f"?곻툘 踰꾪궥 ??? `{video_url}`")
        elif video_url:
            if os.path.exists(video_url):
                try:
                    with open(video_url, "rb") as v_file:
                        vb = v_file.read()
                    render_video(vb)
                except Exception as e:
                    st.error(f"鍮꾨뵒??濡쒕뱶 ?ㅽ뙣: {e}")
                st.caption(f"?뱧 ????꾩튂: `{video_url}`")
                if st.button("?뱛 ?대뜑 ?닿린", key="cached_open_video_folder"):
                    folder_path = os.path.dirname(os.path.abspath(video_url))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":
                        subprocess.Popen(["open", folder_path])
                    else:
                        subprocess.Popen(["xdg-open", folder_path])
            else:
                render_video(video_url)
                st.markdown(f"[?뵕 鍮꾨뵒??留곹겕]({video_url})")
        else:
            st.info("?앹꽦??鍮꾨뵒?ㅺ? ?놁뒿?덈떎.")


def render_pipeline_results(result, show_balloons: bool = False) -> None:
    """?뚯씠?꾨씪???ㅽ뻾 寃곌낵 ?뚮뜑留?""
    import os
    import platform
    import subprocess

    # ?몃꽕??鍮꾨뵒???몄뀡 ???諛?寃곌낵 ?쒖떆
    st.divider()
    st.markdown("### ?럞 ?앹꽦 寃곌낵臾?)

    r_col1, r_col2 = st.columns(2)

    with r_col1:
        st.markdown("#### ?뼹截??몃꽕??)
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
                            f"?좏깮 {idx + 1}",
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
                    f"?곻툘 踰꾪궥 ??? `{SessionManager.get(SessionManager.GENERATED_THUMBNAIL_URL)}`"
                )
            if st.button("?뮶 濡쒖뺄濡????(?몃꽕??", key="save_thumb_local"):
                path = save_thumbnail_bytes(result.generated_content.thumbnail_data)
                SessionManager.set(SessionManager.GENERATED_THUMBNAIL_PATH, path)
                st.caption(f"?뱧 ????꾩튂: `{path}`")
                st.download_button(
                    "燧뉛툘 ?몃꽕???ㅼ슫濡쒕뱶",
                    data=result.generated_content.thumbnail_data,
                    file_name=path.split("\\")[-1],
                    mime="image/png",
                )
            # ?몃꽕??寃쎈줈 (硫붾え由ъ긽???곗씠?곕씪 寃쎈줈媛 ?놁쓣 ???덉쓬, ?????寃쎈줈 ?쒖떆 異붿쿇?섏?留??꾩옱???곗씠?곕쭔 ?덉쓬)
            # 留뚯빟 ?뚯씪濡???λ맂 寃쎈줈媛 ?덈떎硫??쒖떆 (Result 媛앹껜 援ъ“???곕씪 ?ㅻ쫫)
        else:
            st.info("?앹꽦???몃꽕?쇱씠 ?놁뒿?덈떎.")

    with r_col2:
        st.markdown("#### ?렗 鍮꾨뵒??)
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
                    f"?곻툘 踰꾪궥 ??? `{SessionManager.get(SessionManager.GENERATED_VIDEO_URL)}`"
                )
            if st.button("?뮶 濡쒖뺄濡????(鍮꾨뵒??", key="save_video_local"):
                path = save_video_bytes(video_bytes)
                SessionManager.set(SessionManager.GENERATED_VIDEO_PATH, path)
                st.caption(f"?뱧 ????꾩튂: `{path}`")
                st.download_button(
                    "燧뉛툘 鍮꾨뵒???ㅼ슫濡쒕뱶",
                    data=video_bytes,
                    file_name=path.split("\\")[-1],
                    mime="video/mp4",
                )
        elif video_url:
            SessionManager.set(
                SessionManager.GENERATED_VIDEO,
                video_url,
            )

            # 濡쒖뺄 ?뚯씪 泥섎━
            if os.path.exists(video_url):
                # 1. ?붾㈃ ?쒖떆 (諛붿씠?몃줈 ?쎄린)
                try:
                    with open(video_url, "rb") as v_file:
                        video_bytes = v_file.read()
                    render_video(video_bytes)
                except Exception as e:
                    st.error(f"鍮꾨뵒??濡쒕뱶 ?ㅽ뙣: {e}")

                # 2. 寃쎈줈 諛??대뜑 ?닿린
                st.caption(f"?뱧 ????꾩튂: `{video_url}`")

                if st.button("?뱛 ?대뜑 ?닿린", key="open_video_folder"):
                    folder_path = os.path.dirname(os.path.abspath(video_url))
                    if platform.system() == "Windows":
                        os.startfile(folder_path)
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.Popen(["open", folder_path])
                    else:  # Linux
                        subprocess.Popen(["xdg-open", folder_path])
            else:
                # URL??寃쎌슦
                render_video(video_url)
                st.markdown(f"[?뵕 鍮꾨뵒??留곹겕]({video_url})")

        else:
            st.info("?앹꽦??鍮꾨뵒?ㅺ? ?놁뒿?덈떎.")

    # ?꾨왂 ?붿빟 ?쒖떆
    if result.strategy:
        with st.expander("?뱤 留덉????꾨왂 ?붿빟", expanded=True):
            st.write(result.strategy.get("summary", "?붿빟 ?뺣낫 ?놁쓬"))

    # X-Algorithm ?몄궗?댄듃 ?뱀뀡
    if (
        result.collected_data
        and hasattr(result.collected_data, "top_insights")
        and result.collected_data.top_insights
    ):
        st.divider()
        st.markdown("### ?쭬 X-Algorithm ?듭떖 ?몄궗?댄듃")
        st.caption("AI ?뚭퀬由ъ쬁??遺꾩꽍???좏뒠釉??볤? 湲곕컲 怨좉?移??좎옱 怨좉컼???섏씤?ъ씤?몄? 援щℓ ?섎룄")

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
                            <b>?뱦 Keywords:</b> {", ".join(features.get("keywords", [])[:3])}<br>
                            <b>?뮥 Intent:</b> {features.get("purchase_intent", 0):.1f} |
                            <b>?뮠 Viral:</b> {features.get("reply_inducing", 0):.1f}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    if show_balloons:
        st.balloons()
