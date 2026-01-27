import pytest

from genesis_ai.utils.gcs_store import build_gcs_prefix


@pytest.mark.parametrize(
    "name,expected",
    [
        ("Test Product!", "test-product"),
        ("Product/Name\\Test", "product-name-test"),
        ("", "unknown"),
        ("A" * 100, "a" * 50),
    ],
)
def test_build_gcs_prefix_slugify(name, expected):
    result = build_gcs_prefix({"name": name}, "test")
    assert expected in result
