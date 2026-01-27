import os
from datetime import datetime
from pathlib import Path

import pytest

from genesis_ai.core.models.pipeline import (
    CollectedData,
    GeneratedContent,
    PipelineConfig,
    PipelineResult,
)
from genesis_ai.services.history_service import HistoryService
from genesis_ai.utils.file_store import safe_rmtree


@pytest.fixture
def temp_base_dir():
    base_root = Path.cwd() / "tests" / "_tmp_history"
    base_root.mkdir(parents=True, exist_ok=True)
    temp_name = datetime.now().strftime("tmp_%Y%m%d_%H%M%S_%f")
    temp_dir = base_root / temp_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    safe_rmtree(temp_dir)

def test_history_save_and_list(temp_base_dir):
    service = HistoryService(base_dir=temp_base_dir)

    # 1. Mock 데이터 생성
    result = PipelineResult(
        success=True,
        product_name="Test Product",
        config=PipelineConfig(),
        collected_data=CollectedData(top_insights=[{"score": 0.9, "content": "Great!"}]),
        generated_content=GeneratedContent(thumbnail_data=b"fake_image"),
        duration_seconds=10.5,
        executed_at=datetime.now()
    )

    # 2. 저장 테스트
    save_path = service.save_result(result)
    assert os.path.exists(save_path)

    # 3. 목록 조회 테스트
    history = service.get_history_list()
    assert len(history) == 1
    assert history[0]["product_name"] == "Test Product"
    assert history[0]["top_insight_count"] == 1

def test_history_load_and_restore(temp_base_dir):
    service = HistoryService(base_dir=temp_base_dir)

    # 1. 저장
    result = PipelineResult(
        success=True,
        product_name="Restore Product",
        config=PipelineConfig(),
        collected_data=CollectedData(top_insights=[{"score": 0.8, "content": "Insight"}]),
        generated_content=GeneratedContent(video_url="http://gcs/video.mp4"),
        executed_at=datetime.now()
    )
    save_path = service.save_result(result)
    history_id = Path(save_path).stem

    # 2. 로드 테스트
    restored = service.load_history(history_id)
    assert restored is not None
    assert restored.product_name == "Restore Product"
    assert restored.collected_data.top_insights[0]["score"] == 0.8
    assert restored.generated_content.video_url == "http://gcs/video.mp4"
    # 바이트 데이터는 제외되었어야 함
    assert restored.generated_content.thumbnail_data is None

def test_history_delete(temp_base_dir):
    service = HistoryService(base_dir=temp_base_dir)

    # 1. 저장
    result = PipelineResult(
        success=True,
        product_name="Delete Me",
        config=PipelineConfig(),
        executed_at=datetime.now()
    )
    save_path = service.save_result(result)
    history_id = Path(save_path).stem

    # 2. 삭제 테스트
    assert service.delete_history(history_id) is True
    assert not os.path.exists(save_path)
    assert len(service.get_history_list()) == 0
