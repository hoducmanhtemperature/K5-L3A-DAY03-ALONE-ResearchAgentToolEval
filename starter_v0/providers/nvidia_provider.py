from __future__ import annotations

import json
import os
from typing import Any

from providers.base import ModelResponse, ToolCall


class NvidiaProvider:
    """NVIDIA hosted Chat Completions with streamed text and tool arguments."""

    def __init__(self) -> None:
        self.default_model = os.getenv("NVIDIA_MODEL") or "nvidia/nemotron-3.5-super-vl-120b-a12b"

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 1.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        from openai import OpenAI

        key = os.getenv("NVIDIA_API_KEY")
        if not key:
            raise RuntimeError("Missing API key env var: NVIDIA_API_KEY")
        kwargs: dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": 0.95,
            "max_tokens": 16384,
            "seed": 42,
            "stream": True,
            "extra_body": {"chat_template_kwargs": {"enable_thinking": True}},
        }
        if tools:
            kwargs.update(tools=tools, parallel_tool_calls=True)
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        text_parts: list[str] = []
        fragments: dict[int, dict[str, str]] = {}
        finish_reason = None
        # A short retry policy handles transient errors without hiding persistent failures.
        with OpenAI(base_url="https://integrate.api.nvidia.com/v1", api_key=key,
                    timeout=180.0, max_retries=2) as client:
            with client.chat.completions.create(**kwargs) as stream:
                for chunk in stream:
                    if not chunk.choices:
                        continue
                    choice = chunk.choices[0]
                    finish_reason = choice.finish_reason or finish_reason
                    delta = choice.delta
                    if delta.content:
                        text_parts.append(delta.content)
                    for call in delta.tool_calls or []:
                        entry = fragments.setdefault(call.index, {"name": "", "arguments": ""})
                        if call.function:
                            entry["name"] += call.function.name or ""
                            entry["arguments"] += call.function.arguments or ""
        if finish_reason == "length":
            raise RuntimeError("NVIDIA output exceeded max_tokens; response is incomplete")
        calls: list[ToolCall] = []
        for _, entry in sorted(fragments.items()):
            raw_args = entry["arguments"] or "{}"
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                args = {"_invalid_json_arguments": raw_args}
            if not isinstance(args, dict):
                args = {"_invalid_json_arguments": raw_args}
            calls.append(ToolCall(name=entry["name"], args=args))
        return ModelResponse(text="".join(text_parts) or None, tool_calls=calls,
                             raw={"finish_reason": finish_reason})
