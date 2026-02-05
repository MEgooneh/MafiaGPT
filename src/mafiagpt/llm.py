from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Iterable

from openai import OpenAI

from mafiagpt.config import Settings


@dataclass(frozen=True)
class StructuredResponse:
    data: dict[str, Any]

    def require_keys(self, keys: Iterable[str]) -> dict[str, Any]:
        missing = [key for key in keys if key not in self.data]
        if missing:
            raise ValueError(f"Missing keys in structured response: {missing}")
        return self.data


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = OpenAI(api_key=settings.api_key, base_url=settings.base_url)

    def _create_message(self, role: str, content: str) -> dict[str, str]:
        return {"role": role, "content": content}

    def _trim_report(self, intro: str, report: str) -> str:
        max_length = max(self.settings.token_limit - len(intro) - 70, 0)
        if max_length <= 0:
            return ""
        return report[-max_length:]

    def send_structured(
        self, intro: str, game_report: str, command: str
    ) -> StructuredResponse:
        time.sleep(self.settings.rate_limit_seconds)
        context = [
            self._create_message("system", intro),
            self._create_message("user", self._trim_report(intro, game_report)),
            self._create_message("system", command),
        ]
        response = self.client.chat.completions.create(
            model=self.settings.model,
            messages=context,
            temperature=self.settings.temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        if self.settings.debug:
            print(
                "\n".join(
                    [
                        "#######################",
                        intro,
                        "#######################",
                        game_report,
                        "#######################",
                        command,
                        "#######################",
                        json.dumps(data, indent=2),
                    ]
                )
            )
        return StructuredResponse(data=data)
