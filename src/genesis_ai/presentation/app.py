"""
제네시스코리아 스튜디오 - Streamlit 메인 애플리케이션
SOLID 원칙 기반 리팩토링 버전
"""

import streamlit as st

from genesis_ai.config.dependencies import get_services
from genesis_ai.config.products import get_product_by_name, get_product_names
from genesis_ai.config.settings import get_settings
from genesis_ai.presentation.components.log_viewer import setup_global_logging
from genesis_ai.presentation.state.session_manager import SessionManager
from genesis_ai.presentation.styles.neobrutalism import inject_neobrutalism_css

# Tabs Import
from genesis_ai.presentation.tabs import (
    render_ab_test_tab,
    render_analysis_tab,
    render_naver_tab,
    render_pipeline_tab,
    render_report_tab,
    render_social_tab,
    render_thumbnail_tab,
    render_video_tab,
    render_youtube_tab,
)
from genesis_ai.utils.logger import log_app_start, log_error


def main() -> None:
    """메인 애플리케이션"""
    log_app_start()

    # 페이지 설정
    setup_page()

    # 환경 설정
    setup_environment()

    # 세션 상태 초기화
    SessionManager.init_session_state()

    # 스타일 주입
    inject_neobrutalism_css()

    # 사이드바
    render_sidebar()

    # 헤더
    render_header()

    # 메트릭
    render_metrics()

    st.markdown("---")

    # 탭
    render_tabs()

    # 푸터
    render_footer()


def setup_page() -> None:
    """페이지 초기 설정"""
    st.set_page_config(
        page_title="제네시스코리아 스튜디오",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # 전역 로깅 설정 (앱 시작 시 최초 1회)
    setup_global_logging()

def setup_environment() -> None:
    """환경 설정 초기화 - GCP 환경변수 설정"""
    settings = get_settings()
    settings.setup_environment()
    missing = settings.get_missing_required_settings()
    if missing:
        labels = {
            "GOOGLE_CLOUD_PROJECT_ID": "GCP 프로젝트 ID",
            "GOOGLE_API_KEY": "Google API Key",
            "NAVER_CLIENT_ID": "Naver Client ID",
            "NAVER_CLIENT_SECRET": "Naver Client Secret",
        }
        critical_keys = {"GOOGLE_CLOUD_PROJECT_ID", "GOOGLE_API_KEY"}
        critical_missing = [labels.get(k, k) for k in missing if k in critical_keys]
        other_missing = [labels.get(k, k) for k in missing if k not in critical_keys]

        if critical_missing:
            st.error(
                "필수 설정이 누락되어 일부 기능이 동작하지 않을 수 있습니다: "
                + ", ".join(critical_missing)
            )
        if other_missing:
            st.warning(
                "추가 설정이 누락되어 일부 기능이 제한될 수 있습니다: "
                + ", ".join(other_missing)
            )


def render_sidebar() -> None:
    """사이드바 렌더링"""
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">Genesis Korea</div>
                <div class="sidebar-brand-sub">Studio v3.1 Refactored</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")

        # 제품 선택
        product_names = get_product_names()
        selected_name = st.selectbox("제품 선택", product_names)

        if selected_name:
            product = get_product_by_name(selected_name)
            SessionManager.set_selected_product(product)

        st.markdown("---")

        # 저장 경로 설정
        settings = get_settings()
        current_output_dir = settings.app.output_dir
        st.markdown("**📂 저장 폴더 설정**")
        output_dir = st.text_input(
            "저장 폴더",
            value=current_output_dir,
            help="결과물 저장 경로(상대/절대).",
            label_visibility="collapsed",
        )
        output_path = None
        if output_dir:
            import os
            from pathlib import Path

            output_path = Path(output_dir)
            if not output_path.is_absolute():
                output_path = Path.cwd() / output_path

            if output_path.exists() and not output_path.is_dir():
                st.error("저장 폴더 경로가 파일입니다. 폴더 경로를 입력해주세요.")
            else:
                try:
                    output_path.mkdir(parents=True, exist_ok=True)
                    if not os.access(str(output_path), os.W_OK):
                        st.warning("저장 폴더에 쓰기 권한이 없습니다.")
                    else:
                        try:
                            test_file = output_path / ".write_test"
                            test_file.write_text("ok", encoding="utf-8")
                            test_file.unlink(missing_ok=True)
                        except Exception as e:
                            st.warning(f"저장 경로 쓰기 테스트 실패: {e}")
                except Exception as e:
                    st.error(f"저장 폴더 생성/검증 실패: {e}")

            if output_dir != current_output_dir:
                st.session_state["output_dir_override"] = output_dir

        if output_path:
            st.caption(f"현재: `{output_path}`")

        if st.button("💾 저장 폴더 적용", width="stretch"):
            try:
                import datetime
                from pathlib import Path

                env_path = Path(".env")
                lines = []
                backup_name = None
                if env_path.exists():
                    lines = env_path.read_text(encoding="utf-8").splitlines()
                    backup_name = (
                        f".env.backup.{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    env_path.rename(backup_name)
                    env_path = Path(".env")
                    lines = Path(backup_name).read_text(encoding="utf-8").splitlines()

                updated = False
                new_lines = []
                for line in lines:
                    if line.strip().startswith("OUTPUT_DIR="):
                        new_lines.append(f"OUTPUT_DIR={output_dir}")
                        updated = True
                    else:
                        new_lines.append(line)

                if not updated:
                    new_lines.append(f"OUTPUT_DIR={output_dir}")

                env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                st.success("저장 폴더가 적용되었습니다.")
                if backup_name:
                    st.caption(f"백업: `{backup_name}`")
                try:
                    from genesis_ai.utils.logger import log_info

                    log_info(f"OUTPUT_DIR 변경: {output_dir}")
                    history = st.session_state.get("output_dir_history", [])
                    history.append(
                        {
                            "ts": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "path": output_dir,
                        }
                    )
                    st.session_state["output_dir_history"] = history[-20:]
                except Exception as e:
                    log_error(f"OUTPUT_DIR 변경 기록 실패: {e}")
            except Exception as e:
                st.warning(f"저장 실패: {e}")
            st.rerun()
        st.caption("변경 후 적용 버튼을 눌러주세요.")



        with st.expander("☁️ 클라우드 저장 (GCS)", expanded=False):
            current_bucket = get_settings().gcp.gcs_bucket_name or "(미설정)"
            st.caption(f"GCS 연결 상태를 확인합니다. 현재 버킷: `{current_bucket}`")
            if st.button("🔄 설정 다시 읽기", width="stretch"):
                try:
                    from genesis_ai.config.dependencies import ServiceContainer
                    from genesis_ai.config.settings import get_settings as _get_settings

                    _get_settings.cache_clear()
                    ServiceContainer.set_instance(None)
                    st.success("설정을 다시 읽었습니다. 새로고침합니다.")
                    st.rerun()
                except Exception as e:
                    st.error(f"설정 다시 읽기 실패: {e}")
            if st.button("🔍 GCS 연결 확인", width="stretch"):
                try:
                    services = get_services()
                    storage = services.storage_service
                    ok = storage.health_check()
                    if ok:
                        st.success(f"GCS 연결 OK (버킷: {storage.bucket_name})")
                    else:
                        st.warning("GCS 연결 상태를 확인할 수 없습니다.")
                except Exception as e:
                    st.error(f"GCS 연결 확인 실패: {e}")
            if st.button("🧪 GCS 테스트 업로드", width="stretch"):
                try:
                    import datetime

                    services = get_services()
                    storage = services.storage_service
                    test_path = f"healthchecks/{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d_%H%M%S')}.txt"
                    storage.upload(b"gcs-ok", path=test_path, content_type="text/plain")
                    storage.delete(test_path)
                    st.success("GCS 테스트 업로드 성공")
                except Exception as e:
                    message = str(e)
                    if "403" in message or "Permission" in message:
                        st.error(
                            "GCS 테스트 업로드 실패 (권한 부족).\n"
                            "서비스 계정에 아래 권한 중 하나가 필요합니다:\n"
                            "- roles/storage.objectAdmin\n"
                            "- roles/storage.admin"
                        )
                    else:
                        st.error(f"GCS 테스트 업로드 실패: {e}")

        st.markdown("---")
        st.caption("© 2026 Google Cloud")


def render_header() -> None:
    """메인 헤더 렌더링"""
    product = SessionManager.get_selected_product()
    title = getattr(product, "name", "제네시스코리아 스튜디오")

    st.title(title)
    if product:
        st.markdown(f"**{getattr(product, 'description', '')}**")


def render_metrics() -> None:
    """상단 메트릭 렌더링 (예시)"""
    st.caption("상단 메트릭 준비 중입니다.")


def render_tabs() -> None:
    """메인 탭 렌더링"""
    tab_names = [
        "🚀 자동화",
        "📺 YouTube",
        "🛒 네이버",
        "📊 분석",
        "🖼️ 썸네일",
        "🎬 비디오",
        "🧪 A/B 테스트",
        "📱 SNS",
        "📄 리포트",
    ]
    tabs = st.tabs(tab_names)

    with tabs[0]:
        render_pipeline_tab()
    with tabs[1]:
        render_youtube_tab()
    with tabs[2]:
        render_naver_tab()
    with tabs[3]:
        render_analysis_tab()
    with tabs[4]:
        render_thumbnail_tab()
    with tabs[5]:
        render_video_tab()
    with tabs[6]:
        render_ab_test_tab()
    with tabs[7]:
        render_social_tab()
    with tabs[8]:
        render_report_tab()


def render_footer() -> None:
    """푸터 렌더링"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666;'>
            Built with ❤️ by Genesis Korea using Google Cloud Vertex AI
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
