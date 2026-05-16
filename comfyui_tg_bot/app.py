from __future__ import annotations

from dataclasses import dataclass

from comfyui_tg_bot.bot import TelegramBotService
from comfyui_tg_bot.comfyui_client import ComfyUIClient
from comfyui_tg_bot.config import Settings, load_settings
from comfyui_tg_bot.gemini_parser import GeminiParser
from comfyui_tg_bot.job_queue import GenerationQueue
from comfyui_tg_bot.storage import Storage
from comfyui_tg_bot.workflow_registry import WorkflowRegistry


@dataclass(slots=True)
class Application:
    settings: Settings
    storage: Storage
    workflow_registry: WorkflowRegistry
    gemini_parser: GeminiParser
    comfyui_client: ComfyUIClient
    queue: GenerationQueue
    bot: TelegramBotService

    def startup_check(self) -> None:
        self.storage.ensure_directories()
        self.workflow_registry.load()


def create_app() -> Application:
    settings = load_settings()
    storage = Storage(settings=settings)
    workflow_registry = WorkflowRegistry(settings.workflow_dir)
    gemini_parser = GeminiParser(api_key=settings.gemini_api_key)
    comfyui_client = ComfyUIClient(
        base_url=settings.comfyui_base_url,
        timeout_seconds=settings.generation_timeout_seconds,
    )
    queue = GenerationQueue()
    bot = TelegramBotService(
        token=settings.telegram_bot_token,
        queue=queue,
        parser=gemini_parser,
        workflow_registry=workflow_registry,
        comfyui_client=comfyui_client,
        storage=storage,
    )

    return Application(
        settings=settings,
        storage=storage,
        workflow_registry=workflow_registry,
        gemini_parser=gemini_parser,
        comfyui_client=comfyui_client,
        queue=queue,
        bot=bot,
    )
