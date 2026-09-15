import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot import (
    TELEGRAM_BOT_TOKEN,
    start,
    status,
    syncx,
    handle_message,
    error_handler,
)


def main():
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        CommandHandler("syncx", syncx)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.add_error_handler(error_handler)

    external_url = os.environ.get("RENDER_EXTERNAL_URL")

    if not external_url:
        raise RuntimeError("RENDER_EXTERNAL_URL is missing")

    port = int(os.environ.get("PORT", "10000"))
    webhook_path = "telegram"
    webhook_url = f"{external_url.rstrip('/')}/{webhook_path}"

    print(f"MUBA AI webhook is running at {webhook_url}")

    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=webhook_path,
        webhook_url=webhook_url,
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
