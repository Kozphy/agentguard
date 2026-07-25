from __future__ import annotations

import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def generate(self, model: str, prompt: str) -> str:
        response = httpx.post(
            f"{self.base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        value = data.get("response")
        if not isinstance(value, str):
            raise RuntimeError("Ollama returned an invalid response payload")
        return value
