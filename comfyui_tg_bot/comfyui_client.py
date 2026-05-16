from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Any
from urllib.parse import quote

import aiohttp


class ComfyUIClient:
    def __init__(self, base_url: str, timeout_seconds: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def submit_prompt(self, graph: dict[str, Any]) -> str:
        """Submit a prompt to ComfyUI and return the prompt ID."""
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": graph,
            "client_id": prompt_id,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/prompt",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise RuntimeError(f"ComfyUI submit failed: {resp.status} {text}")
                data = await resp.json()
                return data.get("prompt_id", prompt_id)

    async def wait_for_image(self, prompt_id: str) -> tuple[bytes, str]:
        """Wait for image generation to complete and return the image bytes and filename."""
        start_time = time.time()
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < self.timeout_seconds:
                try:
                    async with session.get(
                        f"{self.base_url}/history/{prompt_id}",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        if resp.status == 200:
                            history = await resp.json()
                            if prompt_id in history:
                                outputs = history[prompt_id].get("outputs", {})
                                result = await self._extract_image_from_outputs(session, outputs)
                                if result:
                                    return result
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

                await asyncio.sleep(1)

        raise TimeoutError(f"Image generation timed out after {self.timeout_seconds} seconds")

    async def _extract_image_from_outputs(
        self, session: aiohttp.ClientSession, outputs: dict[str, Any]
    ) -> tuple[bytes, str] | None:
        """Extract image bytes and filename from ComfyUI outputs."""
        for output_data in outputs.values():
            if isinstance(output_data, dict):
                images = output_data.get("images", [])
                if images:
                    image_info = images[0]
                    if isinstance(image_info, dict):
                        filename = image_info.get("filename")
                        subfolder = image_info.get("subfolder", "")
                        if filename:
                            image_bytes = await self._download_image(session, filename, subfolder)
                            return (image_bytes, filename)
        return None

    async def _download_image(
        self, session: aiohttp.ClientSession, filename: str, subfolder: str = ""
    ) -> bytes:
        """Download image from ComfyUI server with proper URL encoding."""
        encoded_filename = quote(filename, safe="")
        url = f"{self.base_url}/view?filename={encoded_filename}"
        if subfolder:
            encoded_subfolder = quote(subfolder, safe="")
            url += f"&subfolder={encoded_subfolder}"

        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Failed to download image: {resp.status}")
            return await resp.read()