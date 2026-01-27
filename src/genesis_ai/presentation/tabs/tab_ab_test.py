from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.utils.media import render_video
from genesis_ai.utils.logger import log_error, log_section, log_success, log_user_action


def render_ab_test_tab() -> None:
    """A/B 테스트 탭 렌더링"""
    st.markdown("### 🧪 A/B 테스트 (Video Style Comparison)")
    st.caption("서로 다른 두 가지 스타일의 영상을 동시에 생성하여 비교합니다.")

    product = SessionManager.get_selected_product()
    if not product:
        st.warning("제품을 먼저 선택해주세요.")
        return

    # 설정 섹션
    st.markdown("---")

    # X-Algorithm 인사이트 기반 추천 버튼
    collected_data = SessionManager.get("collected_data")
    top_insights = []
    if collected_data:
        if hasattr(collected_data, "top_insights"):
            top_insights = collected_data.top_insights
        elif isinstance(collected_data, dict):
            top_insights = collected_data.get("top_insights", [])

    if top_insights:
        if st.button("🧠 X-Algorithm 인사이트 기반 AI 추천 설정", width="stretch"):
            # 상위 2개 인사이트 추출
            ins1 = top_insights[0] if len(top_insights) > 0 else {}
            ins2 = top_insights[1] if len(top_insights) > 1 else ins1

            # 스타일 추천 (랜덤 또는 규칙 기반)
            styles_map = {
                "purchase_intent": "드라마틱",
                "reply_inducing": "유머러스",
                "constructive_feedback": "다큐멘터리",
                "sentiment_intensity": "CGI",
            }

            # A안 추천
            feat1 = ins1.get("features", {})
            if feat1:
                best_feat1 = max(
                    feat1.items(),
                    key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                )[0]
            else:
                best_feat1 = ""
            st.session_state["style_a"] = styles_map.get(best_feat1, "드라마틱")
            keywords1 = ", ".join(feat1.get("keywords", [])[:2])
            st.session_state["hook_a"] = (
                f"[{keywords1}] {ins1.get('content', '')[:30]}..."
            )

            # B안 추천
            feat2 = ins2.get("features", {})
            if feat2:
                best_feat2 = max(
                    feat2.items(),
                    key=lambda x: x[1] if isinstance(x[1], (int, float)) else 0,
                )[0]
            else:
                best_feat2 = ""
            st.session_state["style_b"] = styles_map.get(best_feat2, "유머러스")
            keywords2 = ", ".join(feat2.get("keywords", [])[:2])
            st.session_state["hook_b"] = (
                f"[{keywords2}] {ins2.get('content', '')[:30]}..."
            )

            st.toast("💡 인사이트를 바탕으로 최적의 A/B 테스트 조합이 설정되었습니다.")
            st.rerun()

    c1, c2 = st.columns(2)

    with c1:
        with st.container():
            st.markdown(
                '<div class="ab-panel-marker ab-panel-a"></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### 🅰️ Option A (레드팀)")
            style_a = st.selectbox(
                "스타일 A 선택",
                ["드라마틱", "미니멀", "모던", "레트로"],
                index=0,
                key="style_a",
            )
            hook_a = st.text_input(
                "후킹 문구 A",
                value=f"{getattr(product, 'name', '')}의 강렬한 시작!",
                key="hook_a",
            )

    with c2:
        with st.container():
            st.markdown(
                '<div class="ab-panel-marker ab-panel-b"></div>',
                unsafe_allow_html=True,
            )
            st.markdown("#### 🅱️ Option B (블루팀)")
            style_b = st.selectbox(
                "스타일 B 선택",
                ["유머러스", "CGI", "다큐멘터리", "핸드헬드"],
                index=0,
                key="style_b",
            )
            hook_b = st.text_input(
                "후킹 문구 B",
                value=f"{getattr(product, 'name', '')}의 재미있는 반전!",
                key="hook_b",
            )

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button(
        "⚔️ A/B 테스트 배틀 시작 (영상 동시 생성)",
        width="stretch",
        type="primary",
    ):
        log_section("A/B 테스트 시작")
        log_user_action("A/B 테스트 요청", f"A={style_a}, B={style_b}")

        try:
            services = get_services()

            # 진행 상황 표시
            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("🤖 Gemini가 두 가지 스타일을 분석 중입니다...")
            progress_bar.progress(10)

            status_text.text("🎬 두 가지 스타일 영상을 동시에 생성 중입니다...")
            progress_bar.progress(20)

            prompts = {
                "a": (
                    f"Style: {style_a}. Hook: {hook_a}. Product: {getattr(product, 'name', '')}"
                ),
                "b": (
                    f"Style: {style_b}. Hook: {hook_b}. Product: {getattr(product, 'name', '')}"
                ),
            }

            results = {}
            errors = {}
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_map = {
                    executor.submit(
                        services.video_service.generate,
                        prompt=prompt,
                        duration_seconds=8,
                    ): key
                    for key, prompt in prompts.items()
                }

                for future in as_completed(future_map):
                    key = future_map[future]
                    try:
                        results[key] = future.result()
                    except Exception as e:
                        errors[key] = e

                    completed = len(results) + len(errors)
                    progress = 20 + int((completed / 2) * 80)
                    progress_bar.progress(progress)

            if errors:
                for key, err in errors.items():
                    log_error(f"A/B 테스트 {key.upper()} 영상 생성 실패: {err}")
                status_text.text("❌ 일부 영상 생성 실패")
                st.error(
                    "영상 생성 중 일부가 실패했습니다. 오류 로그를 확인하고 다시 시도해주세요."
                )
                return

            video_a = results.get("a")
            video_b = results.get("b")
            status_text.text("✅ 배틀 준비 완료!")

            # 결과 저장
            if video_a and video_b:
                SessionManager.set(
                    "ab_test_result",
                    {
                        "a": {"style": style_a, "video": video_a, "hook": hook_a},
                        "b": {"style": style_b, "video": video_b, "hook": hook_b},
                    },
                )
                log_success("A/B 테스트 영상 생성 완료")
                st.rerun()
            else:
                st.error("영상 생성 중 일부가 실패했습니다. 다시 시도해주세요.")

        except Exception as e:
            log_error(f"A/B 테스트 중 오류: {e}")
            st.error(f"오류 발생: {e}")

    # 결과 표시 및 투표
    result = SessionManager.get("ab_test_result")
    if result:
        st.divider()
        st.subheader("📊 결과 투표 (승자를 선택하세요)")

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown(
                f"""<div class="neo-container pink" style="text-align: center;">
                    <h3>🅰️ Option A</h3>
                    <p>{result["a"]["style"]} / {result["a"]["hook"]}</p>
                </div>""",
                unsafe_allow_html=True,
            )
            render_video(result["a"]["video"])
            if st.button("👈 A안 승리!", width="stretch", key="vote_a"):
                st.balloons()
                st.toast("🎉 A안이 승리했습니다! 이 스타일을 메인으로 추천합니다.")
                log_user_action("A/B 테스트 선택", "Option A")

        with col_b:
            st.markdown(
                f"""<div class="neo-container blue" style="text-align: center;">
                    <h3>🅱️ Option B</h3>
                    <p>{result["b"]["style"]} / {result["b"]["hook"]}</p>
                </div>""",
                unsafe_allow_html=True,
            )
            render_video(result["b"]["video"])
            if st.button("👉 B안 승리!", width="stretch", key="vote_b"):
                st.snow()
                st.toast("🎉 B안이 승리했습니다! 이 스타일을 메인으로 추천합니다.")
                log_user_action("A/B 테스트 선택", "Option B")
