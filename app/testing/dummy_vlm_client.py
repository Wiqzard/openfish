from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any

import httpx


class DummyVlmClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8010", api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self, scenario: str | None = None) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if scenario:
            headers["X-Dummy-VLM-Scenario"] = scenario
        return headers

    async def chat_completion(
        self,
        *,
        model: str = "dummy-plan",
        text: str = "Analyze this screenshot.",
        image_url: str = "data:image/png;base64,ZmFrZQ==",
        scenario: str | None = None,
    ) -> httpx.Response:
        payload: dict[str, Any] = {
            "model": model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You are a dummy OpenFish test model."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": text},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                },
            ],
        }

        async with httpx.AsyncClient() as client:
            return await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(scenario),
            )

    async def health(self) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            return await client.get(f"{self.base_url}/health")


async def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Call the OpenFish dummy VLM server.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--model", default="dummy-plan")
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--text", default="Analyze this screenshot for OpenFish testing.")
    args = parser.parse_args()

    client = DummyVlmClient(base_url=args.base_url)
    response = await client.chat_completion(
        model=args.model,
        scenario=args.scenario,
        text=args.text,
    )
    print(f"status={response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except ValueError:
        print(response.text)


def main() -> None:
    asyncio.run(_run_cli())


if __name__ == "__main__":
    main()
