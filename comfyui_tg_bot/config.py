from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


class Settings(BaseModel):
    telegram_bot_token: str = ""
    gemini_api_key: str = ""
    comfyui_base_url: str = "http://127.0.0.1:8188"
    workflow_dir: Path = Path("workflow")
    log_dir: Path = Path("logs")
    output_dir: Path = Path("output")
    generation_timeout_seconds: int = Field(
        default=180,
        gt=0,
    )

    @property
    def latest_output_dir(self) -> Path:
        return self.output_dir / "latest"

    @property
    def missing_secrets(self) -> list[str]:
        missing: list[str] = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")
        return missing


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        comfyui_base_url=os.getenv("COMFYUI_BASE_URL", "http://127.0.0.1:8188"),
        workflow_dir=Path(os.getenv("WORKFLOW_DIR", "workflow")),
        log_dir=Path(os.getenv("LOG_DIR", "logs")),
        output_dir=Path(os.getenv("OUTPUT_DIR", "output")),
        generation_timeout_seconds=int(os.getenv("GENERATION_TIMEOUT_SECONDS", "180")),
    )
