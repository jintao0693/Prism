"""生视频任务定义（队列化占位）。"""


async def enqueue_generate_video(*_args, **_kwargs) -> str:
    """投递生视频任务。"""
    raise NotImplementedError("队列化生视频将在 Worker 就绪后启用")
