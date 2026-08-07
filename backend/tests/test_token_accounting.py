"""Token accounting config integration."""

from unittest.mock import patch

import pytest

from backend.core.config import AppConfig
from backend.domain.metrics.token_usage import TokenUsage
from backend.infrastructure.metrics.token_accounting import (
    TokenAccountingService,
    _price_per_token,
)


def _minimal_config(**overrides) -> AppConfig:
    base = dict(
        web_host="0.0.0.0",
        web_port=19407,
        graph_recursion_limit=80,
        max_revisions=3,
        data_dir=__import__("pathlib").Path("/tmp/data"),
        use_server_storage=True,
        database_url="postgresql://localhost/test",
        openrouter_api_key="",
        openai_api_key="",
        openrouter_model="m",
        openai_model="m",
        openrouter_base_url="",
        openrouter_site_url="",
        openrouter_app_name="",
        openai_base_url="",
        crossref_verify=True,
        tavily_api_key="",
        openalex_mailto="",
        semantic_scholar_api_key="",
        chrome_path="",
        chromium_flags="",
        llm_input_usd_per_token=None,
        llm_output_usd_per_token=None,
    )
    base.update(overrides)
    return AppConfig(**base)


def test_price_per_token_uses_config_override():
    cfg = _minimal_config(llm_input_usd_per_token=0.001, llm_output_usd_per_token=0.002)
    with patch("backend.infrastructure.metrics.token_accounting.get_config", return_value=cfg):
        assert _price_per_token("input") == 0.001
        assert _price_per_token("output") == 0.002


def test_token_accounting_records_cost_from_config():
    cfg = _minimal_config(llm_input_usd_per_token=1.0, llm_output_usd_per_token=2.0)
    service = TokenAccountingService()
    usage = TokenUsage(input_tokens=10, output_tokens=5)
    with patch("backend.infrastructure.metrics.token_accounting.get_config", return_value=cfg):
        metrics = service.record("job-1", usage, agent="writer")

    assert metrics.estimated_cost_usd == pytest.approx(20.0)  # 10*1 + 5*2
