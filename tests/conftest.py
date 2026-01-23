"""
Pytest 설정 및 픽스처
"""
import sys
from pathlib import Path

import pytest

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_product():
    """테스트용 샘플 제품"""
    return {
        "name": "벅스델타",
        "category": "해충방제",
        "description": "델타메트린 기반 희석형 광역살충제",
        "target": "모든 해충",
    }


@pytest.fixture
def sample_youtube_data():
    """테스트용 YouTube 데이터"""
    return {
        "videos": [
            {
                "video_id": "abc123",
                "title": "해충 퇴치 방법",
                "description": "효과적인 해충 퇴치",
                "channel": "테스트 채널",
            }
        ],
        "pain_points": [
            {"text": "효과가 없어요", "keyword": "효과없", "likes": 10}
        ],
        "gain_points": [
            {"text": "정말 좋아요", "keyword": "좋아", "likes": 20}
        ],
    }


@pytest.fixture
def sample_naver_data():
    """테스트용 네이버 쇼핑 데이터"""
    return {
        "products": [
            {
                "product_id": "123",
                "title": "해충 퇴치제",
                "price": 15000,
                "brand": "블루가드",
                "mall": "스마트스토어",
            }
        ],
        "competitor_stats": {
            "min_price": 10000,
            "max_price": 30000,
            "avg_price": 18000,
        },
    }
