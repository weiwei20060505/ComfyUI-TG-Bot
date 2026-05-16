from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from io import BytesIO

from telegram import InputFile, Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

from comfyui_tg_bot.comfyui_client import ComfyUIClient
from comfyui_tg_bot.gemini_parser import GeminiParser
from comfyui_tg_bot.job_queue import GenerationQueue
from comfyui_tg_bot.models import GenerationJob
from comfyui_tg_bot.storage import Storage
from comfyui_tg_bot.workflow_registry import WorkflowRegistry
from comfyui_tg_bot.workflow_renderer import render_workflow

logger = logging.getLogger(__name__)


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
        self.app = Application.builder().token(token).build()

    async def run(self) -> None:
        """Run the Telegram bot."""
        # 1. 註冊訊息處理器，過濾掉指令 (例如 /start)，只接收純文字
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # 2. 初始化機器人應用程式
        await self.app.initialize()
        
        # 3. 啟動機器人本體
        await self.app.start()
        
        # 4. 啟動接收 Telegram 訊息的輪詢機制 (取代原本錯誤的 updatesIssuer)
        await self.app.updater.start_polling()
        
        # 5. 在背景建立一個非同步任務，用來不斷處理排隊中的畫圖要求
        asyncio.create_task(self._process_queue())
        
        try:
            # 6. 建立一個無限迴圈，讓主程式永遠保持醒著，不會執行完就關閉
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            # 7. 當我們手動終止程式 (例如按 Ctrl+C) 時，觸發取消錯誤，這裡選擇安靜地忽略
            pass
        finally:
            # 8. 程式即將關閉前，安全地停止輪詢與機器人，釋放資源
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming message from user."""
        if not update.message or not update.message.text:
            await update.message.reply_text("目前只支援文字描述。請傳送您想要的圖片描述。")
            return

        user_prompt = update.message.text.strip()
        chat_id = update.message.chat_id
        user_id = update.message.from_user.id if update.message.from_user else chat_id

        job = GenerationJob(
            chat_id=chat_id,
            user_id=user_id,
            prompt=user_prompt,
        )

        try:
            await update.message.reply_text("已收到需求，正在理解畫面...")
            await self.queue.enqueue(job)
        except Exception as e:
            logger.error(f"Failed to enqueue job: {e}")
            await update.message.reply_text("伺服器目前休息中或過載，請稍後再試")

    async def _process_queue(self) -> None:
        """Process jobs from the generation queue."""
        while True:
            try:
                job = await self.queue.get()
                await self._process_job(job)
                self.queue.task_done()
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
                self.queue.task_done()

    async def _process_job(self, job: GenerationJob) -> None:
        """Process a single generation job."""
        job.started_at = datetime.utcnow()
        
        try:
            await self._send_status_update(job.chat_id, "正在排隊生成")
            
            parse_result = await self.parser.parse(job.prompt, self.workflow_registry)
            job.parse_result = parse_result
            job.workflow_id = parse_result.workflow_id
            
            await self._send_status_update(job.chat_id, "正在生成圖片")
            
            config = self.workflow_registry.get_config(parse_result.workflow_id)
            graph = self.workflow_registry.get_graph(parse_result.workflow_id)
            rendered_graph = render_workflow(graph, config, parse_result)
            
            prompt_id = await self.comfyui_client.submit_prompt(rendered_graph)
            image_bytes = await self.comfyui_client.wait_for_image(prompt_id)
            
            self.storage.save_latest_image(image_bytes)
            
            photo = InputFile(BytesIO(image_bytes), filename="generated.png")
            await self.app.bot.send_photo(chat_id=job.chat_id, photo=photo)
            
            job.finished_at = datetime.utcnow()
            self._log_success(job)
            
        except TimeoutError as e:
            await self._send_status_update(
                job.chat_id, "伺服器目前休息中或過載，請稍後再試"
            )
            job.finished_at = datetime.utcnow()
            self._log_error(job, "TIMEOUT", str(e))
            
        except Exception as e:
            logger.error(f"Error processing job {job.chat_id}: {e}", exc_info=True)
            await self._send_status_update(
                job.chat_id, "伺服器目前休息中或過載，請稍後再試"
            )
            job.finished_at = datetime.utcnow()
            self._log_error(job, type(e).__name__, str(e))

    async def _send_status_update(self, chat_id: int, message: str) -> None:
        """Send status update to user."""
        try:
            await self.app.bot.send_message(chat_id=chat_id, text=message)
        except Exception as e:
            logger.error(f"Failed to send status update to {chat_id}: {e}")

    def _log_success(self, job: GenerationJob) -> None:
        """Log successful generation."""
        prompt_preview = ""
        if job.parse_result:
            prompt_preview = job.parse_result.positive_prompt[:50]
            aspect_ratio = job.parse_result.aspect_ratio
        else:
            aspect_ratio = ""
            
        message = (
            f"chat_id={job.chat_id} user_id={job.user_id} "
            f"workflow_id={job.workflow_id} "
            f"positive_prompt={prompt_preview} "
            f"aspect_ratio={aspect_ratio} "
            f"status=success duration={self._get_duration(job):.1f}s"
        )
        self.storage.append_request_log(message)

    def _log_error(self, job: GenerationJob, error_type: str, error_message: str) -> None:
        """Log error."""
        error_log = (
            f"error_type={error_type} chat_id={job.chat_id} user_id={job.user_id} "
            f"workflow_id={job.workflow_id} message={error_message}"
        )
        self.storage.append_error_log(error_log)

    def _get_duration(self, job: GenerationJob) -> float:
        """Get job duration in seconds."""
        if job.started_at and job.finished_at:
            return (job.finished_at - job.started_at).total_seconds()
        return 0.0