import asyncio
import logging
import os
import yaml
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


class AgentManager:
    def __init__(self, config, core):
        self.config = config
        self.core = core
        self._agents_cfg = self._load_agents_cfg()
        self._history = {}  # agent_name -> list of messages
        self._max_history = 40

    def _load_agents_cfg(self) -> dict:
        p = Path("config/agents.yaml")
        if not p.exists():
            return {}
        with open(p) as f:
            data = yaml.safe_load(f)
        return data.get("agents", {})

    async def run_agent(self, agent_name: str, prompt: str) -> str:
        cfg = self._agents_cfg.get(agent_name)
        if not cfg:
            raise ValueError(f"unknown agent: {agent_name}")

        model = cfg["model"]
        system = cfg.get("system", "")
        max_tokens = cfg.get("max_tokens", 512)
        temperature = cfg.get("temperature", 0.7)
        api_key_env = cfg.get("api_key_env", "ANTHROPIC_API_KEY")

        # seed from persistent memory if no in-process history
        if agent_name not in self._history:
            self._history[agent_name] = []

        self._history[agent_name].append({"role": "user", "content": prompt})
        self._trim_history(agent_name)

        if "claude" in model:
            result = await self._run_anthropic(
                model, system, self._history[agent_name], max_tokens, temperature,
                api_key_env=api_key_env,
            )
        elif "gpt" in model:
            result = await self._run_openai(
                model, system, self._history[agent_name], max_tokens, temperature,
                api_key_env=cfg.get("api_key_env", "OPENAI_API_KEY"),
            )
        else:
            raise ValueError(f"unknown model family: {model}")

        self._history[agent_name].append({"role": "assistant", "content": result})
        self.core.memory.record("assistant", result, agent=agent_name)
        return result

    async def _run_anthropic(self, model, system, messages, max_tokens, temperature, api_key_env):
        import anthropic
        key = os.environ.get(api_key_env, "")
        client = anthropic.AsyncAnthropic(api_key=key)
        msg = await client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=messages,
            temperature=temperature,
        )
        return msg.content[0].text

    async def _run_openai(self, model, system, messages, max_tokens, temperature, api_key_env):
        from openai import AsyncOpenAI
        key = os.environ.get(api_key_env, "")
        client = AsyncOpenAI(api_key=key)
        msgs = [{"role": "system", "content": system}] + messages
        resp = await client.chat.completions.create(
            model=model,
            messages=msgs,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content

    def _trim_history(self, agent_name: str):
        h = self._history[agent_name]
        if len(h) > self._max_history:
            # drop oldest pairs (keep even count for role balance)
            drop = len(h) - self._max_history
            if drop % 2 != 0:
                drop += 1
            self._history[agent_name] = h[drop:]

    def get_history(self, agent_name: str) -> list:
        return self._history.get(agent_name, [])

    def clear_history(self, agent_name: str):
        self._history[agent_name] = []
        log.info("cleared history for agent: %s", agent_name)

    def get_personalities(self) -> dict:
        return {
            name: {
                "model": cfg.get("model"),
                "tools": cfg.get("tools", []),
                "system_preview": cfg.get("system", "")[:80],
            }
            for name, cfg in self._agents_cfg.items()
        }

    def route(self, intent: str) -> str:
        intent = intent.lower()
        if any(w in intent for w in ("move", "wave", "look", "expression", "speak")):
            return "actor"
        if any(w in intent for w in ("see", "observe", "watch", "sensor", "distance")):
            return "observer"
        return "observer"

    async def route_and_run(self, prompt: str) -> str:
        agent_name = self.route(prompt)
        self.core.memory.record("user", prompt)
        return await self.run_agent(agent_name, prompt)

PERSONALITY_NOTES = {
    "observer": "analytical. dry. reports facts without embellishment.",
    "actor": "precise. minimal. moves things when needed.",
    "narrator": "sardonic. british. two sentences max.",
}

def describe_agent(name: str) -> str:
    return PERSONALITY_NOTES.get(name, "unknown agent")
