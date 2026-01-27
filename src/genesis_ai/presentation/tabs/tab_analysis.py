import os
import tempfile
from datetime import datetime

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.styles.neobrutalism import render_metric_card
from genesis_ai.utils.error_handler import safe_action
from genesis_ai.utils.logger import (
    log_data,
    log_section,
    log_success,
    log_user_action,
)


def render_analysis_tab() -> None:
    """분석 탭"""
    st.markdown("### 📊 마케팅 분석")

    if not SessionManager.has_collected_data():
        st.warning("먼저 데이터를 수집해주세요.")
        return

    services = get_services()

    # === 탭 구성: AI 분석, 댓글 분석, CTR 예측 ===
    analysis_tab, comment_tab, ctr_tab = st.tabs(
        ["🤖 AI 전략 분석", "💬 댓글 분석", "📈 CTR 예측"]
    )

    with analysis_tab:
        _render_ai_strategy_section(services)

    with comment_tab:
        _render_comment_analysis_section(services)

    with ctr_tab:
        _render_ctr_prediction_section(services)


def _render_ai_strategy_section(services) -> None:
    """AI 전략 분석 섹션"""
    if st.button("🤖 AI 분석 실행", width="stretch"):
        log_section("AI 마케팅 분석")
        log_user_action("AI 분석 실행 버튼 클릭")
        perform_ai_analysis(services)

    # 전략 표시
    strategy = SessionManager.get(SessionManager.PIPELINE_STRATEGY)
    if strategy:
        display_strategy_report(strategy)
        _render_export_section(services, strategy)


@safe_action(context="AI 마케팅 분석")
def perform_ai_analysis(services) -> None:
    """AI 분석 실행 로직"""
    with st.spinner("Gemini가 데이터를 분석하고 전략을 수립하는 중..."):
        collected_data = SessionManager.get("collected_data")
        if not collected_data:
            st.error("데이터가 없습니다.")
            return

        # top_insights 추출 (모델 또는 딕셔너리 대응)
        top_insights = []
        if hasattr(collected_data, "top_insights"):
            top_insights = collected_data.top_insights
        elif isinstance(collected_data, dict):
            top_insights = collected_data.get("top_insights", [])

        strategy = services.marketing_service.analyze_data(
            product_name=getattr(SessionManager.get_selected_product(), "name", ""),
            youtube_data=getattr(collected_data, "youtube_data", {}),
            naver_data=getattr(collected_data, "naver_data", {}),
            top_insights=top_insights,
        )

        SessionManager.set(SessionManager.PIPELINE_STRATEGY, strategy)

        log_success("마케팅 전략 수립 완료")
        log_data("전략 키워드", len(strategy.get("keywords", [])), "Gemini")

        st.success("분석 완료! 아래 리포트나 PDF 내보내기를 확인하세요.")
        st.rerun()


def display_strategy_report(strategy: dict) -> None:
    """전략 리포트 UI 표시"""
    st.divider()
    st.markdown(f"### 🎯 {strategy.get('product_name', '제품')} 분석 리포트")

    target_audience = strategy.get("target_audience", {})
    if isinstance(target_audience, dict):
        ta_text = f"**Primary**: {target_audience.get('primary', '-')}\n\n"
        ta_text += f"**Secondary**: {target_audience.get('secondary', '-')}\n\n"
        pain_points = target_audience.get("pain_points", [])
        if pain_points:
            ta_text += "**😟 Pain Points**:\n" + "\n".join(
                [f"- {p}" for p in pain_points]
            )
    else:
        ta_text = str(target_audience)

    competitor_analysis = strategy.get("competitor_analysis", {})
    differentiators = competitor_analysis.get("differentiators", [])
    if not differentiators:
        differentiators = strategy.get("unique_selling_point", ["N/A"])
    kv_text = (
        "\n".join([f"- {d}" for d in differentiators])
        if isinstance(differentiators, list)
        else str(differentiators)
    )

    c1, c2 = st.columns(2)
    with c1:
        st.info(f"**👥 타겟 오디언스**\n\n{ta_text}")
    with c2:
        st.success(f"**💎 핵심 가치 (차별화)**\n\n{kv_text}")

    st.markdown("#### 💡 주요 인사이트")
    summary = strategy.get("summary", "")
    if summary:
        st.markdown(f"> {summary}")

    keywords = strategy.get("keywords", [])
    if keywords:
        st.caption(f"키워드: {', '.join(keywords)}")

    content_strategy = strategy.get("content_strategy", {})
    posting_tips = content_strategy.get("posting_tips", [])
    if posting_tips:
        with st.expander("📌 포스팅 꿀팁"):
            for tip in posting_tips:
                st.write(f"- {tip}")

    st.markdown("#### 🎣 추천 훅 (Hook)")
    for hook in strategy.get("hook_suggestions", []):
        st.code(hook, language="text")


def _render_comment_analysis_section(services) -> None:
    """댓글 분석 섹션"""
    st.markdown("#### 💬 YouTube 댓글 분석")
    st.caption("수집된 댓글에서 고객 인사이트를 추출합니다.")

    collected_data = SessionManager.get("collected_data", {})
    if hasattr(collected_data, "model_dump"):
        collected_data = collected_data.model_dump()

    youtube_data = collected_data.get("youtube_data", {})
    comments = youtube_data.get("comments", [])

    if not comments:
        st.warning("분석할 댓글이 없습니다. 먼저 YouTube 데이터를 수집해주세요.")
        return

    st.info(f"📊 총 {len(comments)}개 댓글 분석 가능")

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
            "🔍 기본 분석 (Fast)", key="btn_comment_analysis", width="stretch"
        ):
            perform_comment_analysis(services, comments)
    with col2:
        if st.button(
            "🧠 AI 심층 분석 (Deep)",
            key="btn_deep_analysis",
            width="stretch",
            type="primary",
        ):
            perform_deep_comment_analysis(services, comments)

    # 분석 결과 표시
    analysis = SessionManager.get("comment_analysis")
    if analysis:
        display_comment_analysis(analysis)


@safe_action(context="댓글 기본 분석")
def perform_comment_analysis(services, comments) -> None:
    """댓글 기본 분석 실행"""
    with st.spinner("댓글을 분석하고 있습니다..."):
        analysis = services.comment_analysis_service.analyze_comments(comments)
        SessionManager.set("comment_analysis", analysis)
        st.success("댓글 분석 완료!")
        st.rerun()


@safe_action(context="AI 심층 댓글 분석")
def perform_deep_comment_analysis(services, comments) -> None:
    """AI 심층 댓글 분석 실행"""
    with st.spinner("Gemini가 댓글 속 숨겨진 니즈를 파악하는 중..."):
        analysis = services.comment_analysis_service.analyze_with_ai(comments)
        SessionManager.set("comment_analysis", analysis)
        st.success("AI 심층 분석 완료!")
        st.rerun()


def display_comment_analysis(analysis: dict) -> None:
    """댓글 분석 결과 표시"""
    sentiment = analysis.get("sentiment", {})

    # 감정 분석 차트 (Neo-Brutalism Cards)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            render_metric_card(
                "😊", f"{sentiment.get('positive', 0)}%", "긍정 반응", "mint"
            ),
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            render_metric_card(
                "😐", f"{sentiment.get('neutral', 0)}%", "중립 반응", "blue"
            ),
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            render_metric_card(
                "😟", f"{sentiment.get('negative', 0)}%", "부정 반응", "pink"
            ),
            unsafe_allow_html=True,
        )

    # === AI 인사이트 (Deep Analysis) ===
    ai_data = analysis.get("ai_analysis")
    if ai_data and not ai_data.get("error"):
        st.markdown("---")
        st.markdown("#### 🧠 AI 심층 인사이트 (Gemini Pro)")

        # 1. 고객 감정 & 원인
        cust_sentiment = ai_data.get("customer_sentiment", {})
        if cust_sentiment:
            st.info(
                f"**{cust_sentiment.get('dominant_emotion', '감정')}**: {cust_sentiment.get('sentiment_reason', '')}"
            )

        # 2. Deep Pain Points & Buying Factors
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("🔥 Deep Pain Points")
            st.caption("고객이 실제로 겪는 불편함")
            for pp in ai_data.get("deep_pain_points", []):
                st.error(f"- {pp}")

        with c2:
            st.subheader("💳 Buying Factors")
            st.caption("구매 결정적 요인")
            for bf in ai_data.get("buying_factors", []):
                st.success(f"- {bf}")

        # 3. Marketing Hooks
        st.subheader("🪝 Marketing Hooks")
        st.caption("광고 카피로 즉시 사용 가능한 문구")
        for hook in ai_data.get("marketing_hooks", []):
            st.code(hook, language="text")

        # 4. FAQ Candidates
        if ai_data.get("faq_candidates"):
            with st.expander("❓ 잠재적 FAQ (고객 오해 불식)"):
                for faq in ai_data.get("faq_candidates", []):
                    st.write(f"• {faq}")

        st.markdown("---")

    # === X-Algorithm Engagement Drivers ===
    x_insights = analysis.get("x_algorithm_insights")
    if x_insights:
        st.markdown("#### 🚀 Engagement Drivers (X-Algorithm)")
        st.caption("어떤 댓글이 가장 구매와 반응을 유도하는지 분석한 Top-Rank 결과")

        for item in x_insights:
            rank = item.get("rank")
            score = item.get("score", 0.0)
            author = item.get("author", "Anonymous")
            content = item.get("content", "")
            reason = item.get("reason", "")
            feats = item.get("features", {})

            with st.container(border=True):
                c1, c2 = st.columns([1, 4])
                with c1:
                    st.metric(f"Rank {rank}", f"{score:.1f}")
                    st.caption(author)
                with c2:
                    st.write(content)
                    st.info(f"💡 {reason}")

                    # Feature Chips
                    chips = []
                    if feats.get("purchase", 0) > 0.5:
                        chips.append("💳 구매의도 높음")
                    if feats.get("viral", 0) > 0.5:
                        chips.append("🔥 확산 가능성")

                    if chips:
                        st.caption(" | ".join(chips))

        st.markdown("---")

    # === 기본 통계 (Rule-based) ===
    st.markdown("##### 📌 키워드 통계")

    # Pain/Gain Points (Legacy support)
    col_pain, col_gain = st.columns(2)

    with col_pain:
        st.caption("언급된 불만 키워드 (통계)")
        for point in analysis.get("pain_points", []):
            st.warning(point[:80] + "..." if len(point) > 80 else point)

    with col_gain:
        st.caption("언급된 긍정 키워드 (통계)")
        for point in analysis.get("gain_points", []):
            st.success(point[:80] + "..." if len(point) > 80 else point)

    # FAQ (Legacy)
    questions = analysis.get("questions", [])
    if questions:
        with st.expander("❓ 질문 패턴 (단어 매칭)"):
            for q in questions:
                st.write(f"• {q}")

    # 키워드
    keywords = analysis.get("top_keywords", [])
    if keywords:
        st.caption("가장 많이 등장한 단어")
        keyword_text = " | ".join(
            [f"**{k['word']}** ({k['count']})" for k in keywords[:10]]
        )
        st.markdown(keyword_text)


def _render_ctr_prediction_section(services) -> None:
    """CTR 예측 섹션"""
    st.markdown("#### 📈 CTR 예측 시뮬레이터")
    st.caption("제목과 썸네일 조합의 예상 클릭률을 분석합니다.")

    # 제목 입력
    product = SessionManager.get_selected_product()
    default_title = (
        f"{getattr(product, 'name', '제품')} 사용 후기"
        if product
        else "제목을 입력하세요"
    )

    title = st.text_input("📝 영상 제목", value=default_title, key="ctr_title")
    thumbnail_desc = st.text_area(
        "🖼️ 썸네일 설명 (선택)",
        placeholder="예: 얼굴 클로즈업, 밝은 배경, 텍스트 오버레이 포함",
        height=80,
        key="ctr_thumb_desc",
    )

    # 경쟁 제목 입력
    with st.expander("🔄 경쟁 영상 제목 (차별화 분석용)"):
        competitor_titles_raw = st.text_area(
            "경쟁 영상 제목 (줄바꿈으로 구분)",
            placeholder="경쟁 영상 제목 1\n경쟁 영상 제목 2\n경쟁 영상 제목 3",
            height=100,
            key="ctr_competitors",
        )
        competitor_titles = [
            t.strip() for t in competitor_titles_raw.split("\n") if t.strip()
        ]

    if st.button(
        "📊 CTR 예측", key="btn_ctr_predict", width="stretch", type="primary"
    ):
        perform_ctr_prediction(services, title, thumbnail_desc, competitor_titles)

    # 예측 결과 표시
    prediction = SessionManager.get("ctr_prediction")
    if prediction:
        display_ctr_prediction(prediction)


@safe_action(context="CTR 예측")
def perform_ctr_prediction(services, title, thumb_desc, competitors) -> None:
    """CTR 예측 실행"""
    with st.spinner("AI가 CTR을 예측하고 인사이트를 도출하고 있습니다..."):
        import asyncio

        # X-Algorithm 인사이트 확보
        collected_data = SessionManager.get("collected_data")
        top_insights = []
        if hasattr(collected_data, "top_insights"):
            top_insights = collected_data.top_insights
        elif isinstance(collected_data, dict):
            top_insights = collected_data.get("top_insights", [])

        try:
            # 비동기 AI 분석 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            prediction = loop.run_until_complete(
                services.ctr_predictor.predict_with_ai(
                    title=title,
                    category="marketing",
                    top_insights=top_insights,
                )
            )
            loop.close()

            # 기본 분석 요소 추가 (이미지 설명 등)
            basic = services.ctr_predictor.predict_ctr(
                title=title,
                thumbnail_description=thumb_desc,
                competitor_titles=competitors,
            )
            # 합치기
            prediction.update({
                "breakdown": basic.get("breakdown", {}),
                "total_score": basic.get("total_score", 0),
                "predicted_ctr": basic.get("predicted_ctr", 0),
                "grade": basic.get("grade", "C"),
                "ctr_range": basic.get("ctr_range", ""),
            })

        except Exception as e:
            st.warning(f"AI 심층 분석 실패 ({e}), 기본 예측을 수행합니다.")
            prediction = services.ctr_predictor.predict_ctr(
                title=title,
                thumbnail_description=thumb_desc,
                competitor_titles=competitors,
            )

        SessionManager.set("ctr_prediction", prediction)


def display_ctr_prediction(prediction: dict) -> None:
    """CTR 예측 결과 표시"""
    st.divider()

    # 메인 메트릭
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🎯 예상 CTR", f"{prediction.get('predicted_ctr', 0)}%")
    with col2:
        st.metric("📊 종합 점수", f"{prediction.get('total_score', 0)}/100")
    with col3:
        grade = prediction.get("grade", "C")
        grade_colors = {"S": "🏆", "A": "🥇", "B": "🥈", "C": "🥉", "D": "📉"}
        st.metric("등급", f"{grade_colors.get(grade, '')} {grade}")

    st.info(f"📍 {prediction.get('ctr_range', '')}")

    # 세부 점수
    with st.expander("📋 세부 점수 분석"):
        breakdown = prediction.get("breakdown", {})
        for key, score in breakdown.items():
            label_map = {
                "title_length": "📏 제목 길이",
                "emoji_usage": "😊 이모지 사용",
                "hook_strength": "🎣 후킹 강도",
                "thumbnail": "🖼️ 썸네일",
                "differentiation": "💡 차별화",
            }
            st.progress(int(score) / 100, text=f"{label_map.get(key, key)}: {score}점")

    # 권장사항
    recommendations = prediction.get("recommendations", [])
    if recommendations:
        st.markdown("##### 💡 개선 권장사항")
        for rec in recommendations:
            st.write(rec)

    # AI 심층 분석 결과
    ai_analysis = prediction.get("ai_analysis")
    if ai_analysis:
        with st.expander("🧠 AI 심층 분석 & 대안 제안", expanded=True):
            st.markdown(ai_analysis)


def _render_export_section(services, strategy) -> None:
    """리포트 내보내기 섹션 (분석 탭 내부용)"""
    st.divider()
    st.subheader("📤 리포트 내보내기")

    col_pdf, col_notion = st.columns(2)

    with col_pdf:
        if st.button("📄 PDF 다운로드", width="stretch"):
            log_user_action("PDF 다운로드 요청")
            perform_pdf_export(services, strategy)

    with col_notion:
        if st.button("📝 Notion 내보내기", width="stretch"):
            log_user_action("Notion 내보내기 요청")
            perform_notion_export(services, strategy)


@safe_action(context="PDF 리포트 생성")
def perform_pdf_export(services, strategy) -> None:
    with st.spinner("PDF 생성 중..."):
        export_service = services.export_service
        export_data = {
            "product": {"name": strategy.get("product_name", "제품")},
            "analysis": strategy,
            "metrics": {
                "pain_points": [
                    {"keyword": p}
                    for p in strategy.get("target_audience", {}).get("pain_points", [])
                ],
                "gain_points": [
                    {"keyword": d} for d in strategy.get("unique_selling_point", [])
                ],
            },
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
        output_path = os.path.join(tempfile.gettempdir(), filename)

        pdf_path = export_service.export_pdf(export_data, output_path)

        with open(pdf_path, "rb") as f:
            st.download_button(
                label="⬇️ PDF 파일 저장",
                data=f,
                file_name=filename,
                mime="application/pdf",
                width="stretch",
            )
        log_success(f"PDF 생성 완료: {pdf_path}")
        st.success("PDF 생성 완료!")


@safe_action(context="Notion 페이지 생성")
def perform_notion_export(services, strategy) -> None:
    with st.spinner("Notion 페이지 생성 중..."):
        export_service = services.export_service
        export_data = {
            "product": {"name": strategy.get("product_name", "제품")},
            "analysis": strategy,
            "metrics": {},
        }
        page_url = export_service.export_notion(export_data)

        log_success(f"Notion 페이지 생성 완료: {page_url}")
        st.success(f"Notion 페이지 생성 완료! [바로가기]({page_url})")
