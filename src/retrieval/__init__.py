from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "build_agent": ("retrieval.agent", "build_agent"),
    "run_agent_question": ("retrieval.agent", "run_agent_question"),
    "MiniLMEmbeddings": ("retrieval.embeddings", "MiniLMEmbeddings"),
    "LocalEmbeddingIndex": ("retrieval.index", "LocalEmbeddingIndex"),
    "SearchResult": ("retrieval.index", "SearchResult"),
    "build_llm": ("retrieval.llm", "build_llm"),
    "AnswerResult": ("retrieval.qa", "AnswerResult"),
    "answer_question": ("retrieval.qa", "answer_question"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    if name not in _EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attribute_name = _EXPORTS[name]
    return getattr(import_module(module_name), attribute_name)
