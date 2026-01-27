from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from genesis_ai.utils.file_store import safe_rmtree, safe_unlink


def _make_temp_dir() -> Path:
    base_root = Path.cwd() / "tests" / "_tmp_file_store"
    base_root.mkdir(parents=True, exist_ok=True)
    temp_name = datetime.now().strftime("tmp_%Y%m%d_%H%M%S_%f")
    temp_dir = base_root / temp_name
    temp_dir.mkdir(parents=True, exist_ok=True)
    return temp_dir


def test_safe_unlink_success():
    temp_dir = _make_temp_dir()
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")

    assert safe_unlink(test_file) is True
    assert not test_file.exists()
    safe_rmtree(temp_dir)


def test_safe_unlink_retry_on_permission_error():
    temp_dir = _make_temp_dir()
    test_file = temp_dir / "locked.txt"
    test_file.write_text("test")

    call_count = 0
    original_unlink = Path.unlink

    def mock_unlink(self):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise PermissionError("File locked")
        original_unlink(self)

    with patch.object(Path, "unlink", mock_unlink):
        result = safe_unlink(test_file, retries=3, delay=0.01)

    assert result is True
    assert call_count == 3
    safe_rmtree(temp_dir)


def test_safe_unlink_max_retries_exceeded():
    temp_dir = _make_temp_dir()
    test_file = temp_dir / "always_locked.txt"
    test_file.write_text("test")

    with patch.object(Path, "unlink", side_effect=PermissionError("Always locked")):
        with pytest.raises(PermissionError):
            safe_unlink(test_file, retries=3, delay=0.01)
    safe_rmtree(temp_dir)


def test_safe_rmtree_success():
    temp_dir = _make_temp_dir()
    test_dir = temp_dir / "dir"
    test_dir.mkdir()
    (test_dir / "nested.txt").write_text("test")

    assert safe_rmtree(test_dir) is True
    safe_rmtree(temp_dir)


def test_safe_rmtree_retry_on_permission_error():
    temp_dir = _make_temp_dir()
    test_dir = temp_dir / "locked_dir"
    test_dir.mkdir()
    (test_dir / "nested.txt").write_text("test")

    call_count = 0

    def mock_rmtree(path):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise PermissionError("Dir locked")
        for child in path.iterdir():
            child.unlink()
        path.rmdir()

    with patch("shutil.rmtree", mock_rmtree):
        result = safe_rmtree(test_dir, retries=3, delay=0.01)

    assert result is True
    assert call_count == 3
    safe_rmtree(temp_dir)
