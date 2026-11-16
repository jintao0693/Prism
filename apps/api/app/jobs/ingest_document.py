"""文档入库任务（队列化占位）。"""


async def enqueue_ingest_document(*_args, **_kwargs) -> str:
    """投递文档解析与向量化任务。"""
    raise NotImplementedError("异步入库将在 Worker 就绪后启用")
