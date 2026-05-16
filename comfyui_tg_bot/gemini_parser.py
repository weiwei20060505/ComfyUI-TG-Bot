from __future__ import annotations

from comfyui_tg_bot.models import GeminiParseResult
from comfyui_tg_bot.workflow_registry import WorkflowRegistry


class GeminiParser:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    async def parse(self, user_prompt: str, workflows: WorkflowRegistry) -> GeminiParseResult:
        # External Gemini integration will be implemented after the project skeleton.
        return self.fallback_parse(user_prompt=user_prompt, workflows=workflows)

    def fallback_parse(self, user_prompt: str, workflows: WorkflowRegistry) -> GeminiParseResult:
        config = workflows.get_default_config()
        aspect_ratio = str(config.defaults.get("aspect_ratio", next(iter(config.aspect_ratios))))
        negative_prompt = str(config.defaults.get("negative_prompt", "text, watermark"))

        return GeminiParseResult(
            workflow_id=config.id,
            positive_prompt=user_prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            parameters={},
        )
