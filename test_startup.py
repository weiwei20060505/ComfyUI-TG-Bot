#!/usr/bin/env python
"""Quick test to verify the bot structure and imports."""

import sys
import asyncio

def test_imports():
    """Test all critical imports."""
    print("Testing imports...")
    try:
        from google import genai
        print("✓ google.genai imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.genai: {e}")
        return False
    
    try:
        from comfyui_tg_bot.gemini_parser import GeminiParser
        print("✓ GeminiParser imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import GeminiParser: {e}")
        return False
    
    try:
        from comfyui_tg_bot.bot import TelegramBotService
        print("✓ TelegramBotService imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import TelegramBotService: {e}")
        return False
    
    try:
        from comfyui_tg_bot.app import create_app
        print("✓ create_app imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import create_app: {e}")
        return False
    
    return True

def test_syntax():
    """Check Python syntax of key files."""
    import py_compile
    files = [
        "comfyui_tg_bot/gemini_parser.py",
        "comfyui_tg_bot/bot.py",
        "main.py",
    ]
    
    print("\nTesting Python syntax...")
    for filepath in files:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✓ {filepath} syntax OK")
        except py_compile.PyCompileError as e:
            print(f"✗ {filepath} syntax error: {e}")
            return False
    
    return True

def test_config():
    """Test configuration loading."""
    print("\nTesting configuration...")
    try:
        from comfyui_tg_bot.config import load_settings
        settings = load_settings()
        print(f"✓ Configuration loaded")
        print(f"  - ComfyUI URL: {settings.comfyui_base_url}")
        print(f"  - Workflow dir: {settings.workflow_dir}")
        print(f"  - Timeout: {settings.generation_timeout_seconds}s")
        
        if settings.missing_secrets:
            print(f"⚠ Missing secrets: {', '.join(settings.missing_secrets)}")
            print("  → Make sure .env has TELEGRAM_BOT_TOKEN and GEMINI_API_KEY")
        else:
            print("✓ All required secrets are configured")
        
        return True
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        return False

def test_app_creation():
    """Test app creation without running."""
    print("\nTesting app creation...")
    try:
        from comfyui_tg_bot.app import create_app
        app = create_app()
        print("✓ Application created successfully")
        print(f"  - Workflows: {', '.join(app.workflow_registry.workflow_ids)}")
        return True
    except Exception as e:
        print(f"✗ Failed to create app: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("="*60)
    print("ComfyUI Telegram Bot - Startup Test")
    print("="*60)
    
    results = []
    results.append(("Imports", test_imports()))
    results.append(("Syntax", test_syntax()))
    results.append(("Config", test_config()))
    results.append(("App Creation", test_app_creation()))
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(result for _, result in results)
    print("="*60)
    
    if all_passed:
        print("\n✓ All tests passed! The bot is ready to run.")
        print("\nTo start the bot, run:")
        print("  python main.py")
        return 0
    else:
        print("\n✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))