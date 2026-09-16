"""Connect a Telegram bot from the terminal.

    python backend/scripts/connect_bot.py --token 123:ABC --url https://your.app

Validates the token against the Bot API, attaches this Mini App to the bot's
menu button, sets the command list and writes the result into `.env`.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.telegram import WEBHOOK_PATH  # noqa: E402
from app.config import persist_env, settings  # noqa: E402
from app.telegram.botapi import BotApiError, configure_bot  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Attach asStylist to a Telegram bot")
    parser.add_argument("--token", required=True, help="bot token from @BotFather")
    parser.add_argument("--url", required=True, help="public https URL of this app")
    parser.add_argument("--no-persist", action="store_true", help="do not write .env")
    parser.add_argument("--strict", action="store_true", help="turn demo/browser access off")
    args = parser.parse_args()

    try:
        base = args.url.rstrip("/")
        result = configure_bot(
            args.token,
            base,
            webhook_url=f"{base}{WEBHOOK_PATH}",
            webhook_secret=settings.admin_token,
        )
    except BotApiError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1

    bot = result["bot"]
    print(f"✓ бот: @{bot.get('username')} (id {bot.get('id')})")
    print(f"✓ web app: {result['web_app_url']}")
    for action in result["actions"]:
        print(f"  - {action}")

    if not args.no_persist:
        keys = persist_env(
            {
                "TELEGRAM_BOT_TOKEN": args.token,
                "TELEGRAM_WEB_APP_URL": result["web_app_url"],
                "DEMO_MODE": "false" if args.strict else "true",
            }
        )
        print(f"✓ сохранено в .env: {', '.join(keys)}")

    print(f"\nОткройте https://t.me/{bot.get('username')} — кнопка меню уже ведёт в asStylist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
