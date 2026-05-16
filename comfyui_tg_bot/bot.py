from __future__ import annotations

from comfyui_tg_bot.comfyui_client import ComfyUIClient
from comfyui_tg_bot.gemini_parser import GeminiParser
from comfyui_tg_bot.job_queue import GenerationQueue
from comfyui_tg_bot.storage import Storage
from comfyui_tg_bot.workflow_registry import WorkflowRegistry


class TelegramBotService:
    def __init__(
        self,
        token: str,
        queue: GenerationQueue,
        parser: GeminiParser,
        workflow_registry: WorkflowRegistry,
        comfyui_client: ComfyUIClient,
        storage: Storage,
    ) -> None:
        self.token = token
        self.queue = queue
        self.parser = parser
        self.workflow_registry = workflow_registry
        self.comfyui_client = comfyui_client
        self.storage = storage

    async def run(self) -> None:
        raise NotImplementedError("Telegram polling integration is not implemented yet.")
