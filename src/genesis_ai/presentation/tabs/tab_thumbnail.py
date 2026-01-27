import time

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.services.thumbnail_service import PhotorealisticPromptBuilder
from genesis_ai.utils.error_handler import handle_error
from genesis_ai.utils.file_store import save_thumbnail_bytes, save_video_bytes
from genesis_ai.utils.gcs_store import (
    build_gcs_prefix,
    detect_image_ext,
    detect_video_ext,
    gcs_url_for,
)
from genesis_ai.utils.logger import (
    PipelineLogger,
    log_error,
    log_section,
    log_success,
    log_user_action,
)


def render_thumbnail_tab() -> None:
    """썸네일 탭"""
    st.markdown("### 🖼️ AI 썸네일 생성")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    # 제품 딕셔너리 변환
    product_dict = (
        product.model_dump() if hasattr(product, "model_dump") else product.__dict__
    )

    services = get_services()

    # === 스타일 프리셋 선택 ===
    st.markdown("#### 🎨 스타일 선택")

    available_styles = services.thumbnail_service.get_available_styles()
    style_name_map = {style["key"]: style["name"] for style in available_styles}

    col1, col2 = st.columns([1, 2])

    with col1:
        selected_style = st.selectbox(
            "스타일 프리셋",
            options=[s["key"] for s in available_styles],
            format_func=lambda x: next(
                (s["name"] for s in available_styles if s["key"] == x), x
            ),
        )

    with col2:
        style_desc = next(
            (s["description"] for s in available_styles if s["key"] == selected_style),
            "",
        )
        st.caption(f"💡 {style_desc}")

    # 네오브루탈리즘 특수 옵션
    accent_color = None
    if selected_style == "neobrutalism":
        accent_color = st.selectbox(
            "강조 색상",
            options=["yellow", "pink", "blue", "green"],
            format_func=lambda x: {
                "yellow": "🟡 노랑",
                "pink": "🩷 핑크",
                "blue": "🔵 파랑",
                "green": "🟢 초록",
            }[x],
        )

    # 실사형(Photorealistic) 고급 옵션
    if selected_style == "photorealistic":
        with st.expander("📸 실사형 촬영 옵션", expanded=True):
            st.caption("Google AI 이미지 프롬프트 가이드 기반 전문 촬영 설정")

            col_shot, col_light, col_lens = st.columns(3)

            shot_types = PhotorealisticPromptBuilder.get_shot_types()
            with col_shot:
                st.selectbox(
                    "📷 샷 타입",
                    options=[s["key"] for s in shot_types],
                    format_func=lambda x: next(
                        (s["name_ko"] for s in shot_types if s["key"] == x), x
                    ),
                    index=1,  # product
                    key="thumb_shot_type",
                )

            lighting_presets = PhotorealisticPromptBuilder.get_lighting_presets()
            with col_light:
                st.selectbox(
                    "💡 조명",
                    options=[preset["key"] for preset in lighting_presets],
                    format_func=lambda x: next(
                        (preset["name_ko"] for preset in lighting_presets if preset["key"] == x), x
                    ),
                    index=1,  # studio
                    key="thumb_lighting",
                )

            lens_presets = PhotorealisticPromptBuilder.get_lens_presets()
            with col_lens:
                st.selectbox(
                    "🔍 렌즈",
                    options=[preset["key"] for preset in lens_presets],
                    format_func=lambda x: next(
                        (preset["name_ko"] for preset in lens_presets if preset["key"] == x), x
                    ),
                    index=6,  # 50mm standard
                    key="thumb_lens",
                )

    st.divider()

    # === 훅 텍스트 입력 및 생성 ===
    st.markdown("#### 🎣 마케팅 훅 설정")

    with st.expander("🧠 마케팅 심리 모델 적용 (Marketing Psychology)", expanded=False):
        st.caption("사용자 행동 심리학에 기반한 강력한 훅을 생성해보세요.")

        col_hook_style, col_hook_gen = st.columns([2, 1])

        with col_hook_style:
            hook_style_options = {
                "curiosity": "🤔 호기심 (Curiosity)",
                "loss_aversion": "📉 손실 회피 (Loss Aversion)",
                "social_proof": "👥 사회적 증거 (Social Proof)",
                "authority": "👨‍⚕️ 권위 (Authority)",
                "scarcity": "⏳ 희소성 (Scarcity)",
                "zeigarnik": "🧩 미완성 효과 (Zeigarnik)",
            }
            selected_hook_style = st.selectbox(
                "심리 모델 선택",
                options=list(hook_style_options.keys()),
                format_func=lambda x: hook_style_options[x],
            )

        with col_hook_gen:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("✨ 훅 자동 생성", width="stretch"):
                generated_hooks = services.hook_service.generate_hooks(
                    style=selected_hook_style, product=product_dict, count=1
                )
                if generated_hooks:
                    st.session_state["temp_generated_hook"] = generated_hooks[0]
                    st.rerun()

    # 생성된 훅이 있으면 기본값으로 사용
    default_hook = st.session_state.get(
        "temp_generated_hook", f"{product_dict.get('name', '')} 지금 바로!"
    )

    hook_text = st.text_input("최종 훅 텍스트", value=default_hook)

    include_text_overlay = st.checkbox("텍스트 오버레이 포함", value=True)

    # === 썸네일 생성 ===
    if st.button("🎨 썸네일 생성", width="stretch", type="primary"):
        log_section("썸네일 생성")
        log_user_action(
            "썸네일 생성 요청", f"훅='{hook_text}', 스타일={selected_style}"
        )

        try:
            with st.spinner("AI가 썸네일을 생성하고 있습니다..."):
                if selected_style == "neobrutalism" and accent_color:
                    image_data = services.thumbnail_service.generate_neobrutalism(
                        product=product_dict,
                        hook_text=hook_text,
                        accent_color=accent_color,
                    )
                else:
                    image_data = services.thumbnail_service.generate(
                        product=product_dict,
                        hook_text=hook_text,
                        style=selected_style,
                        include_text_overlay=include_text_overlay,
                    )

                if image_data:
                    st.image(
                        image_data, caption=f"Generated Thumbnail ({selected_style})"
                    )
                    st.success("썸네일 생성 완료!")

                    # 세션 저장
                    SessionManager.set(SessionManager.GENERATED_THUMBNAIL, image_data)
                    # 버킷 자동 업로드
                    try:
                        storage = services.storage_service
                        storage.ensure_bucket()
                        prefix = build_gcs_prefix(product_dict, "thumbnail")
                        ext = detect_image_ext(image_data)
                        gcs_path = f"{prefix}/thumbnail{ext}"
                        storage.upload(
                            data=image_data,
                            path=gcs_path,
                            content_type="image/png" if ext == ".png" else "image/jpeg",
                        )
                        url = gcs_url_for(storage, gcs_path)
                        SessionManager.set(SessionManager.GENERATED_THUMBNAIL_URL, url)
                        storage.upload(
                            data={
                                "type": "thumbnail",
                                "product": product_dict,
                                "style": selected_style,
                                "hook_text": hook_text,
                                "thumbnail_url": url,
                            },
                            path=f"{prefix}/metadata.json",
                            content_type="application/json",
                        )
                        st.caption(f"☁️ 버킷 저장 완료: `{url}`")
                    except Exception as e:
                        st.warning(f"GCS 업로드 실패: {e}")

                    # 로컬 저장은 수동
                    if st.button("💾 로컬로 저장 (썸네일)", width="stretch"):
                        path = save_thumbnail_bytes(image_data)
                        SessionManager.set(SessionManager.GENERATED_THUMBNAIL_PATH, path)
                        st.caption(f"📍 저장 위치: `{path}`")
                        st.download_button(
                            "⬇️ 썸네일 다운로드",
                            data=image_data,
                            file_name=path.split("\\")[-1],
                            mime="image/png",
                        )
                    log_success("썸네일 생성 및 세션 저장 완료")

                else:
                    log_error("썸네일 생성 빈 응답")
                    st.error("썸네일 생성에 실패했습니다.")

        except Exception as e:
            log_error(f"썸네일 생성 중 오류: {e}")
            st.error(handle_error(e, "AI 썸네일 생성"))
            st.caption("💡 프롬프트를 다르게 입력하거나 잠시 후 다시 시도해보세요.")

    # === A/B 테스트 세트 생성 ===
    st.divider()
    st.markdown("#### 🔄 A/B 테스트 세트 (3종)")
    st.info(
        "손실 회피, 사회적 증거 등 검증된 심리 모델을 적용하여 3종 세트를 생성합니다."
    )

    if st.button("🧪 3종 세트 동시 생성", width="stretch"):
        log_section("A/B 썸네일 생성")
        log_user_action("A/B 썸네일 생성 요청", f"제품={product_dict.get('name')}")

        try:
            with st.spinner(
                "3가지 스타일의 썸네일을 생성하고 있습니다... (약 30-60초)"
            ):
                # 1. 심리 모델 기반 훅 다양한 스타일로 생성
                target_styles = ["loss_aversion", "social_proof", "authority"]
                hook_map = services.hook_service.generate_multi_style_hooks(
                    product=product_dict, styles=target_styles
                )

                target_hooks = []
                for style in target_styles:
                    if hook_map.get(style):
                        target_hooks.append(
                            hook_map[style][0]
                        )  # 각 스타일별 첫번째 훅 선택

                # 혹시 부족하면 채우기
                while len(target_hooks) < 3:
                    target_hooks.append(f"{product_dict.get('name')} 추천")

                # 2. A/B 테스트 세트 생성 (서비스 추상화 무시하고 클라이언트 호출)
                target_styles_for_thumbs = ["dramatic", "neobrutalism", "vibrant"]
                ab_results = []
                total = len(target_hooks)
                progress = st.progress(0)

                for idx, hook in enumerate(target_hooks):
                    style_key = target_styles_for_thumbs[idx % len(target_styles_for_thumbs)]
                    image = services.thumbnail_service.generate(
                        product=product_dict,
                        hook_text=hook,
                        style=style_key,
                        include_text_overlay=True,
                    )
                    if image:
                        ab_results.append(
                            {
                                "image": image,
                                "hook_text": hook,
                                "style": style_key,
                                "style_name": style_name_map.get(style_key, style_key),
                            }
                        )
                    progress.progress(int(((idx + 1) / total) * 100))

                if ab_results:
                    st.success(f"{len(ab_results)}개의 썸네일 세트 생성 완료!")
                    SessionManager.set("ab_test_thumbnails", ab_results)

                    # 결과 표시
                    cols = st.columns(3)
                    for idx, res in enumerate(ab_results):
                        with cols[idx]:
                            if res.get("image"):
                                st.image(
                                    res["image"],
                                    caption=f"Style: {res.get('style_name', res.get('style', 'N/A'))}",
                                )
                                st.caption(f"🪄 {res.get('hook_text', '')}")
                    if len(ab_results) < 3:
                        st.warning("3종 중 일부만 생성되었습니다. 다시 시도해주세요.")
                else:
                    st.error("A/B 테스트 세트 생성 실패")

        except Exception as e:
            st.error(handle_error(e, "A/B 썸네일 생성"))

    # Image-to-Video 섹션 (썸네일 생성 여부와 관계없이 세션에 있으면 표시)
    image_data = SessionManager.get(SessionManager.GENERATED_THUMBNAIL)
    if image_data:
        st.divider()
        st.markdown("### 🎬 Veo Image-to-Video")
        st.caption("현재 썸네일을 시작 프레임으로 사용하여 영상을 생성합니다.")

        # 썸네일 미리보기 (작게)
        st.image(image_data, width=200, caption="Source Image")

        if st.button(
            "✨ 이 썸네일로 영상 생성하기", key="btn_i2v", width="stretch"
        ):
            # 훅 텍스트가 비어있을 경우 방어 코드
            safe_hook_text = (
                hook_text if hook_text else f"{product_dict.get('name', '제품')}"
            )

            with PipelineLogger("Veo Image-to-Video 생성") as logger:
                logger.log("썸네일 스타일", selected_style)
                logger.log("Hook", safe_hook_text)

                try:
                    services = get_services()
                    logger.step(1, 2, "I2V 프롬프트 구성 중...")

                    # 프롬프트 생성 (Vision-Narrative Bridge 활용 가능하지만 여기서는 간단 버전)
                    i2v_prompt = f"Cinematic movement for {safe_hook_text}, high quality, smooth transition, 4k"

                    logger.step(2, 2, "Veo 비디오 생성 요청 중 (약 1-2분)...")

                    with st.spinner("Veo가 영상을 생성하고 있습니다..."):
                        video_data = services.video_service.generate_from_image(
                            image_bytes=image_data,
                            prompt=i2v_prompt,
                            duration_seconds=8,
                        )

                        if video_data:
                            # 비디오 데이터 타입 체크
                            if isinstance(video_data, bytes):
                                SessionManager.set(
                                    SessionManager.GENERATED_VIDEO, video_data
                                )
                                # 버킷 자동 업로드
                                try:
                                    storage = services.storage_service
                                    storage.ensure_bucket()
                                    prefix = build_gcs_prefix(product_dict, "video")
                                    ext = detect_video_ext(video_data)
                                    gcs_path = f"{prefix}/video{ext}"
                                    storage.upload(
                                        data=video_data,
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
                                            "hook_text": safe_hook_text,
                                            "video_url": url,
                                        },
                                        path=f"{prefix}/metadata.json",
                                        content_type="application/json",
                                    )
                                    st.caption(f"☁️ 버킷 저장 완료: `{url}`")
                                except Exception as e:
                                    st.warning(f"GCS 업로드 실패: {e}")

                                if st.button("💾 로컬로 저장 (비디오)", width="stretch"):
                                    path = save_video_bytes(video_data)
                                    SessionManager.set(
                                        SessionManager.GENERATED_VIDEO_PATH, path
                                    )
                                    st.caption(f"📍 저장 위치: `{path}`")
                                    st.download_button(
                                        "⬇️ 비디오 다운로드",
                                        data=video_data,
                                        file_name=path.split("\\")[-1],
                                        mime="video/mp4",
                                    )
                                logger.success("영상 생성 완료 및 세션 저장")
                                st.success("영상 생성 완료! 비디오 탭에서 확인하세요.")
                                time.sleep(
                                    1
                                )  # 사용자가 메시지를 볼 수 있도록 잠시 대기
                                st.rerun()
                            else:
                                # 문자열인 경우 (GCS 경로 등 메시지)
                                SessionManager.set(
                                    SessionManager.GENERATED_VIDEO, video_data
                                )
                                SessionManager.set(
                                    SessionManager.GENERATED_VIDEO_URL, video_data
                                )
                                st.info(video_data)
                                logger.success(f"생성 요청 완료: {video_data}")
                        else:
                            st.error("영상 생성 결과가 없습니다. (서버 응답 없음)")
                            logger.log("Error", "Empty result")

                except Exception as ve:
                    st.error(handle_error(ve, "Image-to-Video 생성"))
                    # PipelineLogger __exit__에서 에러 로그 출력됨
                    raise ve
