"""Prism 自研 Agent capabilities。"""

from app.services.agent.capabilities.knowledge_rag import register_knowledge_tools
from app.services.agent.capabilities.media_gen import register_media_tools

__all__ = ["register_knowledge_tools", "register_media_tools"]
