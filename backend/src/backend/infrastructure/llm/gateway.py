"""LLM gateway — infrastructure adapter (OpenRouter / OpenAI)."""

from __future__ import annotations

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from backend.infrastructure.langgraph.agent_context import get_current_agent
from backend.infrastructure.metrics.token_accounting import token_accounting
from backend.core.config import get_config
from backend.domain.metrics.token_usage import TokenUsage


def get_llm(*, temperature: float = 0.3, max_tokens: int = 4096) -> ChatOpenAI:
    cfg = get_config()
    api_key = cfg.llm_api_key()
    if not api_key:
        raise RuntimeError(
            "Укажите OPENROUTER_API_KEY или OPENAI_API_KEY в .env"
        )

    use_openrouter = cfg.uses_openrouter()
    model = cfg.llm_model()
    base_url = cfg.llm_base_url()

    kwargs: dict = {
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if use_openrouter:
        kwargs["default_headers"] = {
            "HTTP-Referer": cfg.openrouter_referer(),
            "X-Title": cfg.openrouter_app_name,
        }

    return ChatOpenAI(**kwargs)


def _extract_usage(response: AIMessage) -> TokenUsage | None:
    meta = getattr(response, "response_metadata", None) or {}
    usage = meta.get("token_usage") or meta.get("usage") or {}
    if not usage and hasattr(response, "usage_metadata") and response.usage_metadata:
        usage = response.usage_metadata

    input_tokens = int(usage.get("input_tokens") or usage.get("prompt_tokens") or 0)
    output_tokens = int(
        usage.get("output_tokens") or usage.get("completion_tokens") or 0
    )
    if input_tokens == 0 and output_tokens == 0:
        return None
    return TokenUsage(input_tokens=input_tokens, output_tokens=output_tokens)


def llm_text(llm: ChatOpenAI, prompt: str) -> str:
    response = llm.invoke(prompt)
    usage = _extract_usage(response)
    if usage:
        token_accounting.record_current(usage, agent=get_current_agent())
    return (response.content or "").strip()
