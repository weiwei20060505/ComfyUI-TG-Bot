from __future__ import annotations

import json
import logging

import google.generativeai as genai

from comfyui_tg_bot.models import GeminiParseResult
from comfyui_tg_bot.workflow_registry import WorkflowRegistry

logger = logging.getLogger(__name__)


class GeminiParser:
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def parse(self, user_prompt: str, workflows: WorkflowRegistry) -> GeminiParseResult:
        try:
            return await self._parse_with_gemini(user_prompt, workflows)
        except Exception as e:
            logger.warning(f"Gemini parsing failed: {e}. Using fallback.")
            try:
                return self.fallback_parse(user_prompt=user_prompt, workflows=workflows)
            except Exception as fallback_error:
                logger.error(f"Fallback parsing also failed: {fallback_error}")
                raise

    async def _parse_with_gemini(
        self, user_prompt: str, workflows: WorkflowRegistry
    ) -> GeminiParseResult:
        workflow_descs = self._build_workflow_descriptions(workflows)
        aspect_ratios = self._build_aspect_ratios_desc(workflows)

        gemini_prompt = f"""You are an AI that helps users convert natural language image generation requests into structured parameters.

The user wants to generate an image. Based on their description, you must:
1. Choose the best workflow from the available options
2. Generate detailed English positive and negative prompts
3. Select an appropriate aspect ratio
4. Return ONLY valid JSON without any markdown or explanation

Available workflows:
{workflow_descs}

Supported aspect ratios:
{aspect_ratios}

User request: {user_prompt}

You MUST respond with ONLY valid JSON in this exact format:
{{
  "workflow_id": "test",
  "positive_prompt": "detailed English positive prompt here",
  "negative_prompt": "detailed English negative prompt here",
  "aspect_ratio": "1:1",
  "parameters": {{}}
}}

Important:
- The positive_prompt should be detailed and describe the image scene, style, quality, lighting, etc.
- The negative_prompt should specify unwanted elements
- Choose aspect_ratio from the supported options
- If the user mentions style or composition, incorporate it into the prompts
- Always respond with valid JSON only, no other text"""

        response = self.model.generate_content(gemini_prompt)
        response_text = response.text.strip()

        try:
            result_dict = json.loads(response_text)
        except json.JSONDecodeError:
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text
            result_dict = json.loads(json_str)

        result = GeminiParseResult.model_validate(result_dict)

        if result.workflow_id not in workflows.workflow_ids:
            logger.warning(f"Invalid workflow_id {result.workflow_id}, using default")
            result.workflow_id = workflows.get_default_config().id

        config = workflows.get_config(result.workflow_id)
        if result.aspect_ratio not in config.aspect_ratios:
            logger.warning(f"Invalid aspect_ratio {result.aspect_ratio}, using first available")
            result.aspect_ratio = next(iter(config.aspect_ratios))

        return result

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

    def _build_workflow_descriptions(self, workflows: WorkflowRegistry) -> str:
        lines = []
        for workflow_id, config in workflows.configs.items():
            default_marker = " (default)" if config.is_default else ""
            lines.append(
                f"- {workflow_id}{default_marker}: {config.name} - {config.description}\n"
                f"  Selection hint: {config.selection_hint}"
            )
        return "\n".join(lines)

    def _build_aspect_ratios_desc(self, workflows: WorkflowRegistry) -> str:
        config = workflows.get_default_config()
        lines = []
        for ratio in config.aspect_ratios.keys():
            lines.append(f"- {ratio}")
        return ", ".join(lines)