"""异步 Worker 入口（占位）。

后续接入 Redis 队列后，在此消费：
- generate_image / generate_video
- ingest_document
"""

from __future__ import annotations

import logging
import time

from app.core.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> None:
    """开发期占位循环：提示尚未接入队列。"""
    setup_logging(True)
    logger.info("Prism Worker 已启动（占位模式，未消费真实队列）")
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
