"""Реестр языковых инструментов — подключение по code_language из задания."""

from __future__ import annotations

from backend.infrastructure.adapters.code_language import normalize_code_language
from backend.infrastructure.adapters.code_tools.base import CodeToolkit
from backend.infrastructure.adapters.code_tools.c_toolkit import TOOLKIT as C_TOOLKIT
from backend.infrastructure.adapters.code_tools.cpp_toolkit import TOOLKIT as CPP_TOOLKIT
from backend.infrastructure.adapters.code_tools.java_toolkit import TOOLKIT as JAVA_TOOLKIT
from backend.infrastructure.adapters.code_tools.python_toolkit import TOOLKIT as PYTHON_TOOLKIT
from backend.infrastructure.adapters.code_tools.web_toolkit import TOOLKIT as WEB_TOOLKIT

_REGISTRY: dict[str, CodeToolkit] = {
    "python": PYTHON_TOOLKIT,
    "java": JAVA_TOOLKIT,
    "c": C_TOOLKIT,
    "cpp": CPP_TOOLKIT,
    "javascript": WEB_TOOLKIT,
}

_ALIASES = {
    "js": "javascript",
    "html": "javascript",
    "css": "javascript",
    "web": "javascript",
    "py": "python",
    "c++": "cpp",
}


def get_code_toolkit(language: str) -> CodeToolkit:
    """Вернуть инструмент для языка; по умолчанию Python."""
    key = normalize_code_language(language)
    key = _ALIASES.get(key, key)
    return _REGISTRY.get(key, PYTHON_TOOLKIT)


def supported_languages() -> list[str]:
    return list(_REGISTRY.keys())


def is_web_toolkit(language: str) -> bool:
    return get_code_toolkit(language).screenshot_mode == "browser"
