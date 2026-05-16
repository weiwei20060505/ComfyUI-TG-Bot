from __future__ import annotations

from comfyui_tg_bot.app import create_app


def main() -> None:
    app = create_app()
    app.startup_check()

    print("ComfyUI Telegram bot skeleton is ready.")
    print(f"Loaded workflows: {', '.join(app.workflow_registry.workflow_ids)}")
    print(f"Workflow directory: {app.settings.workflow_dir}")
    print(f"ComfyUI base URL: {app.settings.comfyui_base_url}")


if __name__ == "__main__":
    main()
