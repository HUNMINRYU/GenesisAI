import sys
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from genesis_ai.config.settings import get_settings
from genesis_ai.infrastructure.clients.gemini_client import GeminiClient


def verify_gemini_connection():
    print("🔍 GeminiClient 인증 테스트 시작...")

    try:
        settings = get_settings()
        settings.setup_environment()  # 환경변수 설정 필수!

        print(f"📄 Project ID: {settings.gcp.project_id}")
        print(f"📍 Location: {settings.gcp.location}")

        client = GeminiClient(
            project_id=settings.gcp.project_id, location=settings.gcp.location
        )

        # Health check
        if client.health_check():
            print("✅ GeminiClient 초기화 성공")
        else:
            print("❌ GeminiClient API 연결 실패")
            return

        # Simple generation test
        print("🧪 텍스트 생성 테스트 중...")
        response = client.generate_text("Hello, verify connection.", temperature=0.1)
        print(f"✅ 테스트 응답: {response.strip()}")
        print("\n🎉 모든 인증 테스트 통과!")

    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    verify_gemini_connection()
