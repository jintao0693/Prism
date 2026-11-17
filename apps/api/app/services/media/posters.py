"""视频海报抽帧（优先 ffmpeg）。"""

from __future__ import annotations

import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_video_poster(video_bytes: bytes, *, at_sec: float = 0.5) -> bytes | None:
    """从视频字节抽一帧 JPEG；无 ffmpeg 或失败时返回 None。"""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        logger.warning("未找到 ffmpeg，跳过视频海报抽帧")
        return None

    with tempfile.TemporaryDirectory(prefix="prism_poster_") as tmp:
        root = Path(tmp)
        src = root / "in.mp4"
        dst = root / "poster.jpg"
        src.write_bytes(video_bytes)
        cmd = [
            ffmpeg,
            "-y",
            "-ss",
            str(max(0.0, at_sec)),
            "-i",
            str(src),
            "-frames:v",
            "1",
            "-q:v",
            "4",
            str(dst),
        ]
        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=60,
            )
        except (subprocess.SubprocessError, OSError) as exc:
            logger.warning("视频抽帧失败: %s", exc)
            return None
        if not dst.exists() or dst.stat().st_size < 32:
            return None
        return dst.read_bytes()
