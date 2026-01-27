import os
import sys
import tempfile
from pathlib import Path

# Add src to python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from genesis_ai.infrastructure.clients.notion_client import NotionClient
from genesis_ai.infrastructure.services.pdf_service import PdfService


def verify_export():
    print("🧪 Data Export 기능 테스트 시작...")

    # Mock Data
    mock_data = {
        "product": {"name": "Test Product"},
        "analysis": {
            "target_audience": {
                "primary": "Solo Entrepreneurs",
                "pain_points": ["Time Shortage", "No Design Skills"],
                "desires": ["Automation", "High Quality Output"],
            },
            "hook_suggestions": ["Hook 1", "Hook 2"],
        },
        "metrics": {
            "pain_points": [{"keyword": "Slow"}, {"keyword": "Hard"}],
            "gain_points": [{"keyword": "Fast"}, {"keyword": "Easy"}],
        },
    }

    # 1. PDF Export Test
    print("\n📄 PDF 생성 테스트 중...")
    try:
        service = PdfService()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            output_path = service.export(mock_data, tmp.name)
            print(f"✅ PDF 생성 성공: {output_path}")

            # Check file size
            if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                print(f"✅ 파일 크기 확인: {os.path.getsize(output_path)} bytes")
            else:
                print("❌ PDF 파일이 비어있거나 생성되지 않음")

            os.unlink(output_path)
    except Exception as e:
        print(f"❌ PDF 생성 실패: {e}")
        import traceback

        traceback.print_exc()

    # 2. Notion Client Test (Config check only)
    print("\n📝 Notion Client 설정 테스트 중...")
    try:
        client = NotionClient(api_key="test_key")
        if client.is_configured():
            print("✅ Notion Client 설정 확인")
        else:
            print("❌ Notion Client 설정 실패")
    except Exception as e:
        print(f"❌ Notion Client 테스트 실패: {e}")


if __name__ == "__main__":
    verify_export()
