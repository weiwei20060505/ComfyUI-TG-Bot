from __future__ import annotations

from typing import Any


class ComfyUIClient:
    def __init__(self, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def submit_prompt(self, graph: dict[str, Any]) -> str:
        raise NotImplementedError("ComfyUI API integration is not implemented yet.")

    async def wait_for_image(self, prompt_id: str) -> bytes:
        raise NotImplementedError("ComfyUI image retrieval is not implemented yet.")
