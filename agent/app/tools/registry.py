from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable


ToolHandler = Callable[..., Any | Awaitable[Any]]


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    handler: ToolHandler


@dataclass
class ToolContext:
    conversation_id: str | None = None
    username: str | None = None


class ToolRegistry:
    def __init__(self, allowlist: set[str] | None = None):
        self.allowlist = allowlist or set()
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> None:
        self._tools[spec.name] = spec

    def list_tools(self) -> list[dict[str, str]]:
        return [
            {"name": spec.name, "description": spec.description}
            for spec in self._tools.values()
            if self.is_allowed(spec.name)
        ]

    def is_allowed(self, name: str) -> bool:
        return not self.allowlist or name in self.allowlist

    async def call(self, name: str, args: dict[str, Any], context: ToolContext | None = None) -> Any:
        if not self.is_allowed(name):
            raise PermissionError(f"Tool is not allowed: {name}")
        if name not in self._tools:
            raise KeyError(f"Tool is not registered: {name}")

        handler = self._tools[name].handler
        result = handler(**args, context=context)
        if inspect.isawaitable(result):
            return await result
        return result
