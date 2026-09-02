"""
agents/base_agent.py
====================
Abstract base class for all QE AgentX agents.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import yaml
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI

from config.settings import Settings
from core.mock_llm import MockChain, MockLLM

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent.parent / "config" / "prompts"

OUTPUT_INTEGRITY_RULES = """

GLOBAL OUTPUT INTEGRITY RULES:
- Preserve all relevant facts and previously supplied content unless the task explicitly
    requires updating that exact field.
- Never silently truncate, hide, replace, or omit content. If a limit prevents complete
    output, state that limitation explicitly in the schema field intended for notes or gaps.
- Return only the fields required by the requested output schema; do not replace unrelated
    sections or introduce presentation markup that can obscure structured content.
- Keep labels, identifiers, traceability references, statuses, and terminology consistent
    with the supplied Jira and pipeline context.
"""


class BaseAgent(ABC):
    """
    All agents share:
    - A configured AzureChatOpenAI LLM instance
    - Prompt loading from versioned YAML templates
    - Structured JSON output parsing
    - Uniform error handling that writes to state["errors"]
    """

    agent_name: str = "base"

    def __init__(self, settings: Settings):
        self.settings = settings
        self.is_mock_mode = settings.is_mock_mode

        if self.is_mock_mode:
            logger.warning("[%s] MOCK MODE ENABLED — using deterministic mock responses", self.agent_name)
            self.llm = MockChain(MockLLM())
        else:
            self.llm = AzureChatOpenAI(
                azure_deployment=settings.azure_openai_deployment,
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_key,
                api_version=settings.azure_openai_api_version,
                temperature=0.1,
                max_tokens=4096,
            )
        self._prompt_cache: dict[str, dict] = {}

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    @abstractmethod
    def run(self, state: dict) -> dict:
        """
        Execute agent logic against the shared pipeline state.
        Must return a dict containing updated state keys only.
        Should append to state["errors"] on failure rather than raise,
        so the orchestrator can handle recovery.
        """
        ...

    # ------------------------------------------------------------------ #
    # Protected helpers
    # ------------------------------------------------------------------ #

    def _load_prompt_config(self, agent_name: str) -> dict:
        """Load and cache a prompt YAML file from config/prompts/."""
        if agent_name not in self._prompt_cache:
            prompt_path = PROMPTS_DIR / f"{agent_name}.yaml"
            if not prompt_path.exists():
                raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            with open(prompt_path, encoding="utf-8") as f:
                self._prompt_cache[agent_name] = yaml.safe_load(f)
        return self._prompt_cache[agent_name]

    def _build_chain(self, system_prompt: str, human_template: str):
        """Return a LangChain LCEL chain: prompt | llm | json_parser."""
        if self.is_mock_mode:
            # Mock mode: return the MockChain directly; it handles invoke() calls
            return self.llm

        # Production mode: build a real chain
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt + OUTPUT_INTEGRITY_RULES),
            ("human", human_template),
        ])
        return prompt | self.llm | JsonOutputParser()

    def _safe_run(self, state: dict, func) -> dict:
        """Wrap agent execution with error capture."""
        try:
            return func(state)
        except Exception as exc:
            logger.error("[%s] Agent error: %s", self.agent_name, exc, exc_info=True)
            errors = list(state.get("errors", []))
            errors.append(f"{self.agent_name}: {exc!s}")
            return {"errors": errors}
