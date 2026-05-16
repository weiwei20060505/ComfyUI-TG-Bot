# ComfyUI Telegram Bot

A Python-based Telegram bot that connects to a local ComfyUI instance to generate images from natural language descriptions using Gemini AI.

## Features

- **Natural Language to Image**: Convert text descriptions into images via Telegram
- **Gemini AI Integration**: Automatically parse user prompts and select appropriate workflows
- **Dynamic Workflow Support**: Load workflows and configurations from the `workflow/` directory without code changes
- **Queue Management**: Handle multiple requests sequentially to avoid ComfyUI overload
- **Comprehensive Logging**: Request and error logging for monitoring and debugging
- **Environment-based Configuration**: All sensitive settings in `.env`

## Quick Start

### Prerequisites

- Python 3.14+
- ComfyUI running locally at `http://127.0.0.1:8188` (configurable)
- Telegram Bot Token (from BotFather)
- Gemini API Key (from Google AI Studio)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd comfyui_tg_bot
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment:
```bash
# Edit .env with your Telegram Token and Gemini API Key
```

4. Run the bot:
```bash
python main.py
```

## Configuration

Edit `.env` with the following variables:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
COMFYUI_BASE_URL=http://127.0.0.1:8188
WORKFLOW_DIR=workflow
LOG_DIR=logs
OUTPUT_DIR=output
GENERATION_TIMEOUT_SECONDS=180
```

## Workflow Management

### Adding a New Workflow

1. Place your ComfyUI workflow JSON in `workflow/` folder (e.g., `workflow/my_workflow.json`)
2. Create a corresponding config file (e.g., `workflow/my_workflow.config.json`)

Example config structure:
```json
{
  "id": "my_workflow",
  "name": "My Custom Workflow",
  "description": "Description of what this workflow does",
  "selection_hint": "When to use this workflow",
  "workflow_file": "my_workflow.json",
  "is_default": false,
  "fields": {
    "positive_prompt": {
      "required": true,
      "target": {
        "node_id": "6",
        "input": "text"
      }
    },
    "negative_prompt": {
      "required": true,
      "target": {
        "node_id": "7",
        "input": "text"
      }
    },
    "width": {
      "required": true,
      "target": {
        "node_id": "5",
        "input": "width"
      }
    },
    "height": {
      "required": true,
      "target": {
        "node_id": "5",
        "input": "height"
      }
    }
  },
  "aspect_ratios": {
    "1:1": {"width": 1024, "height": 1024},
    "16:9": {"width": 1344, "height": 768},
    "9:16": {"width": 768, "height": 1344}
  },
  "defaults": {
    "negative_prompt": "text, watermark",
    "aspect_ratio": "1:1"
  }
}
```

## Project Structure

```
comfyui_tg_bot/
├── main.py                    # Entry point
├── comfyui_tg_bot/
│   ├── __init__.py
│   ├── app.py                # Application factory
│   ├── bot.py                # Telegram bot service
│   ├── comfyui_client.py     # ComfyUI API client
│   ├── config.py             # Settings and configuration
│   ├── gemini_parser.py      # Gemini API integration
│   ├── job_queue.py          # Job queue management
│   ├── models.py             # Pydantic models
│   ├── storage.py            # Logging and file storage
│   ├── workflow_registry.py  # Workflow management
│   └── workflow_renderer.py  # Workflow graph manipulation
├── workflow/                 # Workflow files and configs
│   ├── test.json
│   └── test.config.json
├── logs/                     # Generated logs
│   ├── requests.log
│   └── errors.log
├── output/                   # Generated images
│   └── latest/
│       └── latest.png
├── pyproject.toml
└── README.md
```

## How It Works

1. User sends a text message to the Telegram bot
2. Bot acknowledges receipt and sends status updates
3. Gemini AI parses the user's natural language prompt
4. Appropriate workflow is selected based on the request
5. User's prompt is rendered into the workflow
6. Workflow is submitted to ComfyUI
7. Bot waits for image generation to complete
8. Generated image is sent back to the user
9. Request and results are logged for monitoring

## Error Handling

- **Gemini failures**: Automatic retry + fallback to default configuration
- **ComfyUI unavailable**: User-friendly error message with details in error log
- **Generation timeout**: 3-minute timeout with friendly error notification
- **Invalid requests**: Graceful error handling with logging

## Logging

- **requests.log**: All successful generations with parameters and timing
- **errors.log**: Detailed error information for debugging

## Development

### Project Dependencies

- `python-telegram-bot`: Telegram API integration
- `google-genai`: Gemini API client
- `aiohttp`: Async HTTP client for ComfyUI
- `pydantic`: Data validation
- `python-dotenv`: Environment variable management

### Code Style

The project follows PEP 8 with type hints throughout.

## License

MIT License