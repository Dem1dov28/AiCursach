"""Tests for centralized AppConfig."""

from backend.core.config import AppConfig, get_config


def test_app_config_llm_openrouter():
    cfg = AppConfig(
        web_host="0.0.0.0",
        web_port=19407,
        graph_recursion_limit=80,
        max_revisions=3,
        data_dir=__import__("pathlib").Path("/tmp/data"),
        use_server_storage=True,
        database_url="postgresql://localhost/test",
        openrouter_api_key="sk-test",
        openai_api_key="",
        openrouter_model="openai/gpt-4.1-mini",
        openai_model="gpt-4.1-mini",
        openrouter_base_url="https://openrouter.ai/api/v1",
        openrouter_site_url="",
        openrouter_app_name="Test",
        openai_base_url="",
        crossref_verify=True,
        tavily_api_key="",
        openalex_mailto="test@local",
        semantic_scholar_api_key="",
        chrome_path="",
        chromium_flags="",
        llm_input_usd_per_token=None,
        llm_output_usd_per_token=None,
    )
    assert cfg.llm_configured()
    assert cfg.uses_openrouter()
    assert cfg.llm_model() == "openai/gpt-4.1-mini"
    assert cfg.web_url() == "http://localhost:19407"


def test_get_config_is_cached():
    first = get_config()
    second = get_config()
    assert first is second
