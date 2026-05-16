from __future__ import annotations

import asyncio
import logging
import sys

from comfyui_tg_bot.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    try:
        app = create_app()
        app.startup_check()

        logger.info("ComfyUI Telegram bot is starting...")
        logger.info(f"Loaded workflows: {', '.join(app.workflow_registry.workflow_ids)}")
        logger.info(f"Workflow directory: {app.settings.workflow_dir}")
        logger.info(f"ComfyUI base URL: {app.settings.comfyui_base_url}")
        
        if app.settings.missing_secrets:
            logger.error(
                f"Missing required configuration: {', '.join(app.settings.missing_secrets)}"
            )
            sys.exit(1)

        await app.bot.run()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())