"""
GCS 업로드 헬퍼
"""

from __future__ import annotations

import re
from datetime import datetime, timezone


def build_gcs_prefix(product: dict, kind: str) -> str:
    name = product.get("name", "product")
    safe = re.sub(r"[^a-z0-9]+", "-", str(name).lower()).strip("-")
    safe = safe[:50] if safe else "unknown"
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"genesis-korea/{kind}/{safe}/{ts}"


def detect_image_ext(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    return ".bin"


def detect_video_ext(data: bytes) -> str:
    if b"ftyp" in data[:64]:
        return ".mp4"
    return ".bin"


def gcs_url_for(storage, path: str) -> str:
    public = getattr(storage, "get_public_url", lambda p: None)(path)
    if public:
        return public
    bucket = getattr(storage, "bucket_name", "bucket")
    return f"gs://{bucket}/{path}"
