"""日志初始化。"""

import logging
import sys


def setup_logging(debug: bool = False) -> None:
    """配置根日志器。"""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        stream=sys.stdout,
        force=True,
    )
