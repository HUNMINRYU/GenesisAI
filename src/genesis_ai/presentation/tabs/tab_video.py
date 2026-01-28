import io

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.infrastructure.clients.veo_client import AdvancedPromptBuilder
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.utils.media import render_video
from genesis_ai.utils.error_handler import handle_error
from genesis_ai.utils.file_store import save_video_bytes
from genesis_ai.utils.gcs_store import build_gcs_prefix, detect_video_ext, gcs_url_for
from genesis_ai.utils.logger import (
    PipelineLogger,
)


def get_image_bytes_from_session(image_data):
    """세션에 저장된 이미지 데이터를 bytes로 변환"""
    try:
        # 이미 bytes인 경우
        if isinstance(image_data, bytes):
            return image_data

        # PIL Image 객체인 경우 (세션 매니저가 PIL 객체를 저장할 수도 있음)
        if hasattr(image_data, "save"):
            img_byte_arr = io.BytesIO()
            image_data.save(img_byte_arr, format="PNG")
            return img_byte_arr.getvalue()

        # URL인 경우 (현재는 지원하지 않음, 로컬 데이터 가정)
        return None
    except Exception:
        return None


def render_video_tab() -> None:
    """비디오 탭"""
    st.markdown("### 🎬 AI 비디오 생성")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    # 제품 딕셔너리 변환
    product_dict = (
        product.model_dump() if hasattr(product, "model_dump") else product.__dict__
    )

    services = get_services()
    is_generating = SessionManager.get(SessionManager.VIDEO_GENERATING, False)

    # === [New] 썸네일 기반 마케팅 영상 생성 (Vision-Narrative) ===
    st.markdown("#### 🖼️ 썸네일로 시작하기 (Vision-Narrative)")
    st.caption(
        "생성된 썸네일 중 하나를 선택하면, AI가 최적의 영상 기획(프롬프트)을 제안합니다."
    )

    # 세션에서 썸네일 이미지 가져오기 (이미지 생성 탭에서 저장된 데이터)
    # 가정: SessionManager.get("generated_images")에 이미지 리스트가 있음
    generated_images = SessionManager.get("generated_thumbnails", [])

    selected_thumbnail = None
    if generated_images:
        # 썸네일 선택 UI (컬럼 그리드)
        cols = st.columns(min(len(generated_images), 3))
        for idx, img_data in enumerate(generated_images[:3]):  # 최대 3개 표시
            with cols[idx]:
                st.image(img_data, width="stretch", caption=f"후보 {idx + 1}")
                if st.button(
                    f"✅ 선택 ({idx + 1})",
                    key=f"sel_thumb_{idx}",
                    width="stretch",
                ):
                    SessionManager.set("selected_thumbnail_idx", idx)
                    st.rerun()

        # 선택된 인덱스 확인
        sel_idx = SessionManager.get("selected_thumbnail_idx")
        if sel_idx is not None and 0 <= sel_idx < len(generated_images):
            selected_thumbnail = generated_images[sel_idx]
            st.success(f"📌 후보 {sel_idx + 1}번 썸네일이 선택되었습니다.")
    else:
        st.info("💡 이미지 생성 탭에서 먼저 썸네일을 생성해보세요.")

    # 후킹 문구 (기존 로직 유지)
    generated_hooks = SessionManager.get("generated_hooks", [])
    hook_text = ""
    if generated_hooks:
        hook_text = st.selectbox("후킹 대사 (AI 보이스오버)", generated_hooks)
    else:
        hook_text = st.text_input(
            "후킹 대사 직접 입력 (AI 보이스오버)", f"{product_dict.get('name')}!"
        )

    # === Vision 프롬프트 생성 & 영상 제작 ===
    if selected_thumbnail:
        st.divider()
        st.markdown("##### 🧠 AI 프롬프트 분석 및 생성")

        # 프롬프트 생성/수정 UI
        vision_prompt_key = "vision_generated_prompt"
        current_prompt = SessionManager.get(vision_prompt_key, "")

        if st.button(
            "✨ Gemini 프롬프트 생성", type="primary", width="stretch"
        ):
            with PipelineLogger("Veo Vision-Narrative 분석") as logger:
                logger.log("Hook", hook_text)
                try:
                    with st.spinner(
                        "Gemini가 썸네일을 분석하고 스토리를 설계 중입니다..."
                    ):
                        img_bytes = get_image_bytes_from_session(selected_thumbnail)
                        if not img_bytes:
                            st.error("이미지 데이터를 처리할 수 없습니다.")
                            logger.log("Error", "Image data is None")
                        else:
                            logger.step(1, 2, "썸네일 시각적 요소 분석 중...")
                            prompt = (
                                services.video_service.generate_story_prompt_from_image(
                                    image_bytes=img_bytes,
                                    product=product_dict,
                                    hook_text=hook_text,
                                    mode="single",
                                )
                            )
                            logger.step(2, 2, "스토리라인 및 카메라 무브먼트 설계 완료")

                            if prompt:
                                SessionManager.set(vision_prompt_key, prompt)
                                logger.success("프롬프트 생성 완료")
                                st.rerun()
                            else:
                                st.error("프롬프트 생성 실패 (빈 응답)")
                                logger.log("Error", "Empty prompt response")

                except Exception as e:
                    logger.log("Exception", str(e))
                    st.error(handle_error(e, "프롬프트 생성"))

        if current_prompt:
            st.markdown("###### 📝 생성된 프롬프트 (수정 가능)")
            final_prompt = st.text_area(
                "Veo 3.1 프롬프트",
                value=current_prompt,
                height=200,
                help="Gemini가 생성한 영문 프롬프트입니다. 필요하다면 수정하세요.",
            )

            if st.button(
                "🎬 이 프롬프트로 영상 생성",
                type="primary",
                disabled=is_generating,
            ):
                SessionManager.set(SessionManager.VIDEO_GENERATING, True)
                with PipelineLogger("Veo 3.1 비디오 생성") as logger:
                    logger.log("Prompt Length", f"{len(final_prompt)} chars")
                    try:
                        with st.spinner(
                            "Veo가 영상을 생성하고 있습니다... (약 1-2분 소요)"
                        ):
                            # 이미지 기반 생성(I2V) 호출
                            img_bytes = get_image_bytes_from_session(selected_thumbnail)

                            logger.step(1, 1, "Veo 3.1 모델 추론 중...")

                            video_result = services.video_service.generate_from_image(
                                image_bytes=img_bytes,
                                prompt=final_prompt,
                                duration_seconds=8,
                            )

                            if video_result:
                                if isinstance(video_result, bytes):
                                    SessionManager.set(
                                        SessionManager.GENERATED_VIDEO, "bytes"
                                    )
                                    render_video(video_result, format="video/mp4")
                                    # 버킷 자동 업로드
                                    try:
                                        storage = services.storage_service
                                        storage.ensure_bucket()
                                        prefix = build_gcs_prefix(product_dict, "video")
                                        ext = detect_video_ext(video_result)
                                        gcs_path = f"{prefix}/video{ext}"
                                        storage.upload(
                                            data=video_result,
                                            path=gcs_path,
                                            content_type="video/mp4"
                                            if ext == ".mp4"
                                            else "application/octet-stream",
                                        )
                                        url = gcs_url_for(storage, gcs_path)
                                        SessionManager.set(
                                            SessionManager.GENERATED_VIDEO_URL, url
                                        )
                                        storage.upload(
                                            data={
                                                "type": "video",
                                                "product": product_dict,
                                                "prompt": final_prompt,
                                                "video_url": url,
                                            },
                                            path=f"{prefix}/metadata.json",
                                            content_type="application/json",
                                        )
                                        st.caption(f"☁️ 버킷 저장 완료: `{url}`")
                                    except Exception as e:
                                        st.warning(f"GCS 업로드 실패: {e}")

                                    if st.button(
                                        "💾 로컬로 저장 (비디오)",
                                        width="stretch",
                                    ):
                                        path = save_video_bytes(video_result)
                                        SessionManager.set(
                                            SessionManager.GENERATED_VIDEO_PATH, path
                                        )
                                        st.caption(f"📍 저장 위치: `{path}`")
                                        st.download_button(
                                            label="💾 영상 다운로드",
                                            data=video_result,
                                            file_name=path.split("\\")[-1],
                                            mime="video/mp4",
                                        )
                                else:
                                    render_video(video_result)
                                    SessionManager.set(
                                        SessionManager.GENERATED_VIDEO, video_result
                                    )
                                    SessionManager.set(
                                        SessionManager.GENERATED_VIDEO_URL, video_result
                                    )

                                st.success("영상 생성이 완료되었습니다!")
                                logger.success("영상 생성 완료")
                            else:
                                logger.log("Result", "None")
                    except Exception as e:
                        # logger.log("Exception", str(e)) # PipelineLogger가 이미 출력할 수도 있음
                        st.error(handle_error(e, "영상 생성"))
                    finally:
                        SessionManager.set(SessionManager.VIDEO_GENERATING, False)

    st.divider()

    # 기존 수동 설정 UI (접어두기)
    with st.expander("🛠️ 수동 설정 모드 (기존 방식)", expanded=not selected_thumbnail):
        render_manual_mode(product_dict, services, is_generating)


def render_manual_mode(product_dict, services, is_generating):
    """기존 수동 설정 모드 UI"""
    # === 후킹 스타일 선택 섹션 ===
    st.markdown("#### 🎣 후킹 스타일 선택")

    hook_styles = services.hook_service.get_available_styles()

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_style = st.selectbox(
            "후킹 스타일",
            options=[s["key"] for s in hook_styles],
            format_func=lambda x: next(
                (f"{s['emoji']} {s['name']}" for s in hook_styles if s["key"] == x), x
            ),
            help="영상 시작 부분의 훅 스타일을 선택하세요",
            key="manual_style",
        )

    with col2:
        style_desc = next(
            (s["description"] for s in hook_styles if s["key"] == selected_style), ""
        )
        st.info(f"💡 {style_desc}")

    # 후킹 문구 생성/선택
    if st.button("🎣 후킹 문구 생성", key="btn_gen_hooks_manual"):
        hooks = services.hook_service.generate_hooks(
            style=selected_style,
            product=product_dict,
            count=3,
        )
        SessionManager.set("generated_hooks", hooks)

    generated_hooks = SessionManager.get("generated_hooks", [])
    selected_hook = ""
    if generated_hooks:
        selected_hook = st.radio(
            "사용할 후킹 문구 선택", options=generated_hooks, key="radio_hooks_manual"
        )
    else:
        selected_hook = st.text_input(
            "직접 입력",
            value=f"{product_dict.get('name', '제품')} 지금 바로!",
            key="custom_hook_manual",
        )

    st.divider()

    # === 비디오 설정 ===
    st.markdown("#### ⚙️ 비디오 설정")

    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox(
            "비디오 길이", [8, 15, 30], index=0, key="manual_duration"
        )
    with col2:
        resolution = st.selectbox(
            "해상도", ["1080p", "720p"], index=0, key="manual_res"
        )

    # === 고급 옵션 (Expander) ===
    with st.expander("🎥 고급 촬영 옵션", expanded=False):
        st.caption("Google AI 프롬프트 가이드 기반 전문 촬영 설정")

        # 카메라 무브먼트
        camera_movements = AdvancedPromptBuilder.get_camera_movements()
        col_cam, col_comp = st.columns(2)

        with col_cam:
            selected_camera = st.selectbox(
                "📹 카메라 무브먼트",
                options=[c["key"] for c in camera_movements],
                format_func=lambda x: next(
                    (f"{c['name_ko']}" for c in camera_movements if c["key"] == x), x
                ),
                index=2,  # orbit 기본값
                key="sel_camera_manual",
            )
            cam_desc = next(
                (
                    c["description"]
                    for c in camera_movements
                    if c["key"] == selected_camera
                ),
                "",
            )
            st.caption(f"💡 {cam_desc}")

        # 구도
        compositions = AdvancedPromptBuilder.get_compositions()
        with col_comp:
            selected_composition = st.selectbox(
                "🖼️ 구도",
                options=[c["key"] for c in compositions],
                format_func=lambda x: next(
                    (f"{c['name_ko']}" for c in compositions if c["key"] == x), x
                ),
                index=1,  # medium 기본값
                key="sel_comp_manual",
            )

        # 조명 및 오디오
        col_light, col_audio = st.columns(2)

        lighting_moods = AdvancedPromptBuilder.get_lighting_moods()
        with col_light:
            selected_lighting = st.selectbox(
                "💡 조명/분위기",
                options=[preset["key"] for preset in lighting_moods],
                format_func=lambda x: next(
                    (f"{preset['name_ko']}" for preset in lighting_moods if preset["key"] == x), x
                ),
                index=2,  # studio 기본값
                key="sel_light_manual",
            )

        audio_presets = AdvancedPromptBuilder.get_audio_presets()
        with col_audio:
            selected_audio = st.selectbox(
                "🔊 오디오 스타일",
                options=[a["key"] for a in audio_presets],
                format_func=lambda x: next(
                    (f"{a['name_ko']}" for a in audio_presets if a["key"] == x), x
                ),
                index=0,  # cinematic 기본값
                key="sel_audio_manual",
            )

        # SFX 입력
        sfx_input = st.text_input(
            "🎵 효과음 (쉼표로 구분)",
            placeholder="예: 제품 클릭 소리, 상쾌한 음료 따르는 소리",
            key="sfx_input_manual",
        )

        # 주변소음
        ambient_input = st.text_input(
            "🌿 주변소음",
            placeholder="예: 조용한 스튜디오, 카페 배경음",
            key="ambient_input_manual",
        )

    # === 비디오 생성 ===
    if st.button(
        "🎬 비디오 생성",
        width="stretch",
        type="primary",
        key="btn_gen_manual",
        disabled=is_generating,
    ):
        SessionManager.set(SessionManager.VIDEO_GENERATING, True)
        try:
            with st.spinner("AI가 숏폼 비디오를 생성합니다..."):
                # AdvancedPromptBuilder 사용
                prompt_builder = AdvancedPromptBuilder()
                prompt_builder.with_product(
                    product_dict.get("name", "제품"), product_dict.get("category", "")
                )
                prompt_builder.with_marketing_hook(selected_hook)

                # UI에서 선택한 옵션 적용
                prompt_builder.camera_movement = selected_camera
                prompt_builder.composition = selected_composition
                prompt_builder.lighting_mood = selected_lighting
                prompt_builder.audio_preset = selected_audio

                if sfx_input:
                    prompt_builder.sfx = [s.strip() for s in sfx_input.split(",")]
                if ambient_input:
                    prompt_builder.ambient = ambient_input

                # 프롬프트 빌드
                advanced_prompt = prompt_builder.build()

                video_result = services.video_service.generate(
                    prompt=advanced_prompt,
                    duration_seconds=duration,
                    resolution=resolution,
                )

                if video_result:
                    if isinstance(video_result, bytes):
                        SessionManager.set(SessionManager.GENERATED_VIDEO, "bytes")
                        render_video(video_result, format="video/mp4")
                        # 버킷 자동 업로드
                        try:
                            storage = services.storage_service
                            storage.ensure_bucket()
                            prefix = build_gcs_prefix(product_dict, "video")
                            ext = detect_video_ext(video_result)
                            gcs_path = f"{prefix}/video{ext}"
                            storage.upload(
                                data=video_result,
                                path=gcs_path,
                                content_type="video/mp4"
                                if ext == ".mp4"
                                else "application/octet-stream",
                            )
                            url = gcs_url_for(storage, gcs_path)
                            SessionManager.set(
                                SessionManager.GENERATED_VIDEO_URL, url
                            )
                            storage.upload(
                                data={
                                    "type": "video",
                                    "product": product_dict,
                                    "prompt": advanced_prompt,
                                    "video_url": url,
                                },
                                path=f"{prefix}/metadata.json",
                                content_type="application/json",
                            )
                            st.caption(f"☁️ 버킷 저장 완료: `{url}`")
                        except Exception as e:
                            st.warning(f"GCS 업로드 실패: {e}")

                        if st.button("💾 로컬로 저장 (비디오)", width="stretch"):
                            path = save_video_bytes(video_result)
                            SessionManager.set(SessionManager.GENERATED_VIDEO_PATH, path)
                            st.caption(f"📍 저장 위치: `{path}`")
                            st.download_button(
                                "💾 영상 다운로드",
                                data=video_result,
                                file_name=path.split("\\")[-1],
                                mime="video/mp4",
                            )
                    else:
                        render_video(video_result)
                        SessionManager.set(
                            SessionManager.GENERATED_VIDEO, video_result
                        )
                        SessionManager.set(
                            SessionManager.GENERATED_VIDEO_URL, video_result
                        )
                    st.success("비디오 생성 완료!")

                    # 사용된 프롬프트 표시
                    with st.expander("📝 사용된 프롬프트"):
                        st.code(advanced_prompt, language="text")
                else:
                    st.info(
                        "비디오 생성 결과가 반환되지 않았습니다. (백그라운드 처리 중일 수 있음)"
                    )

        except Exception as e:
            st.error(handle_error(e, "AI 비디오 생성"))
            st.caption("💡 비디오 길이를 줄이거나 잠시 후 다시 시도해보세요.")
        finally:
            SessionManager.set(SessionManager.VIDEO_GENERATING, False)
