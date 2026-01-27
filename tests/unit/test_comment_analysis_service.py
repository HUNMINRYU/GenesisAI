from genesis_ai.services.comment_analysis_service import CommentAnalysisService


def test_analyze_comments_empty_returns_defaults():
    service = CommentAnalysisService()

    result = service.analyze_comments([])

    assert result["total_comments"] == 0
    assert result["sentiment"]["neutral"] == 100
    assert result["pain_points"] == []
    assert result["gain_points"] == []
    assert result["questions"] == []


def test_analyze_comments_basic_counts():
    service = CommentAnalysisService()

    comments = [
        {"text": "이거 진짜 좋아요 최고네요", "likes": 10},
        {"text": "완전 별로고 불만입니다", "likes": 1},
        {"text": "가격이 얼마인가요?", "likes": 0},
    ]

    result = service.analyze_comments(comments)

    assert result["total_comments"] == 3
    assert result["sentiment"]["positive"] > 0
    assert result["sentiment"]["negative"] > 0
    assert isinstance(result["top_keywords"], list)
    assert isinstance(result["summary"], str)


def test_analyze_with_ai_without_client_falls_back():
    service = CommentAnalysisService(gemini_client=None)

    comments = [{"text": "좋아요", "likes": 2}]
    result = service.analyze_with_ai(comments)

    assert result["ai_analysis"] is None
