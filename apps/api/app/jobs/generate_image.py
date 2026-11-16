"""生图任务定义（队列化占位）。"""


async def enqueue_generate_image(*_args, **_kwargs) -> str:
    """投递生图任务，返回 job_id。当前由同步 Gateway 直跑。"""
    raise NotImplementedError("队列化生图将在 Worker 就绪后启用")
