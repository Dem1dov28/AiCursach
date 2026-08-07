"""Domain value objects for LLM session metrics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
        )


@dataclass(frozen=True)
class AgentTokenUsage:
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def merge(self, usage: TokenUsage) -> AgentTokenUsage:
        return AgentTokenUsage(
            input_tokens=self.input_tokens + usage.input_tokens,
            output_tokens=self.output_tokens + usage.output_tokens,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "input": self.input_tokens,
            "output": self.output_tokens,
            "total": self.total_tokens,
        }

    @staticmethod
    def empty() -> AgentTokenUsage:
        return AgentTokenUsage(input_tokens=0, output_tokens=0)


@dataclass(frozen=True)
class SessionMetrics:
    tokens_input: int
    tokens_output: int
    estimated_cost_usd: float
    tokens_by_agent: dict[str, AgentTokenUsage] = field(default_factory=dict)

    def to_dict(self) -> dict[str, float | int | dict[str, dict[str, int]]]:
        payload: dict[str, float | int | dict[str, dict[str, int]]] = {
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
            "tokens_total": self.tokens_input + self.tokens_output,
            "estimated_cost_usd": round(self.estimated_cost_usd, 6),
        }
        if self.tokens_by_agent:
            payload["tokens_by_agent"] = {
                agent: usage.to_dict() for agent, usage in self.tokens_by_agent.items()
            }
        return payload

    @staticmethod
    def empty() -> SessionMetrics:
        return SessionMetrics(tokens_input=0, tokens_output=0, estimated_cost_usd=0.0)

    @staticmethod
    def from_usage(
        usage: TokenUsage,
        *,
        cost_usd: float,
        agent: str | None = None,
    ) -> SessionMetrics:
        by_agent: dict[str, AgentTokenUsage] = {}
        if agent:
            by_agent[agent] = AgentTokenUsage(
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
        return SessionMetrics(
            tokens_input=usage.input_tokens,
            tokens_output=usage.output_tokens,
            estimated_cost_usd=cost_usd,
            tokens_by_agent=by_agent,
        )

    def merge(self, other: SessionMetrics) -> SessionMetrics:
        merged_agents = dict(self.tokens_by_agent)
        for agent, usage in other.tokens_by_agent.items():
            current = merged_agents.get(agent, AgentTokenUsage.empty())
            merged_agents[agent] = current.merge(
                TokenUsage(input_tokens=usage.input_tokens, output_tokens=usage.output_tokens)
            )
        return SessionMetrics(
            tokens_input=self.tokens_input + other.tokens_input,
            tokens_output=self.tokens_output + other.tokens_output,
            estimated_cost_usd=self.estimated_cost_usd + other.estimated_cost_usd,
            tokens_by_agent=merged_agents,
        )
