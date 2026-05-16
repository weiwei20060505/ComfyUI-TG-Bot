from __future__ import annotations

from datetime import datetime
from pathlib import Path

from comfyui_tg_bot.config import Settings


class Storage:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def requests_log_path(self) -> Path:
        return self.settings.log_dir / "requests.log"

    @property
    def errors_log_path(self) -> Path:
        return self.settings.log_dir / "errors.log"

    @property
    def latest_image_path(self) -> Path:
        return self.settings.latest_output_dir / "latest.png"

    def ensure_directories(self) -> None:
        self.settings.log_dir.mkdir(parents=True, exist_ok=True)
        self.settings.latest_output_dir.mkdir(parents=True, exist_ok=True)

    def append_request_log(self, message: str) -> None:
        self._append_line(self.requests_log_path, message)

    def append_error_log(self, message: str) -> None:
        self._append_line(self.errors_log_path, message)

    def save_latest_image(self, image_bytes: bytes) -> Path:
        self.settings.latest_output_dir.mkdir(parents=True, exist_ok=True)
        self.latest_image_path.write_bytes(image_bytes)
        return self.latest_image_path

    def _append_line(self, path: Path, message: str) -> None:
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(f"{timestamp} {message}\n")
