import os
import sys
import logging
import asyncio
import threading
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from database.db import DatabaseManager
from database.seed import seed_initial_data
from bot.handlers import register_handlers, set_db_manager
from telegram import Update
from telegram.ext import Application

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8460543006:AAGk6fszUO7NfP6WtblGsD5ecWVkEq3aWxQ")
BOT_STATUS = {"status": "starting", "errors": 0}


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        status_text = f"Bot Status: {BOT_STATUS.get('status', 'ok')} | Errors: {BOT_STATUS.get('errors', 0)}"
        self.wfile.write(status_text.encode("utf-8"))

    def log_message(self, format, *args):
        pass


def start_health_check_server():
    """Starts a background HTTP health check server for Render Web Services."""
    port = int(os.environ.get("PORT", 10000))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        logging.getLogger(__name__).info(f"Health check HTTP server listening on port {port}")
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not start health check HTTP server: {e}")


async def keep_alive_ping():
    """Pings local health check server every 3 minutes to keep Render Web Service active 24/7."""
    logger = logging.getLogger(__name__)
    port = int(os.environ.get("PORT", 10000))
    url = f"http://127.0.0.1:{port}/"
    while True:
        await asyncio.sleep(180)  # Every 3 minutes
        try:
            import urllib.request
            urllib.request.urlopen(url, timeout=5)
            logger.debug("Keep-alive self-ping successful.")
        except Exception as e:
            logger.debug(f"Keep-alive self-ping failed: {e}")


async def run_bot_polling():
    """Resilient async polling loop with automatic error recovery and reconnection."""
    logger = logging.getLogger(__name__)

    # Start self-pinging keep-alive task to prevent Render free service sleep
    asyncio.create_task(keep_alive_ping())

    # Instantiate DatabaseManager and seed initial data
    db_manager = DatabaseManager("automail.db")
    seed_initial_data(db_manager)
    set_db_manager(db_manager)

    while True:
        app = None
        try:
            logger.info("Building Telegram Application...")
            app = Application.builder().token(BOT_TOKEN).build()
            app.bot_data["db_manager"] = db_manager

            # Register handlers
            register_handlers(app)

            logger.info("Initializing and starting Telegram Polling...")
            await app.initialize()
            await app.start()
            await app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=False
            )

            BOT_STATUS["status"] = "running"
            logger.info("✅ Auto Mail Bot is ACTIVE and listening for Telegram updates!")

            # Keep active
            while app.updater.running:
                await asyncio.sleep(10)

        except Exception as e:
            BOT_STATUS["errors"] += 1
            BOT_STATUS["status"] = f"error: {e}"
            logger.error(f"❌ Exception in bot polling loop: {e}\n{traceback.format_exc()}")
            logger.info("Restarting polling loop in 5 seconds...")
            
            if app:
                try:
                    if app.updater and app.updater.running:
                        await app.updater.stop()
                    if app.running:
                        await app.stop()
                    await app.shutdown()
                except Exception as shutdown_err:
                    logger.debug(f"Cleanup error during shutdown: {shutdown_err}")

            await asyncio.sleep(5)


def main() -> None:
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    logger.info("Initializing Auto Mail Telegram Bot...")

    # Start health check server for Render web service port health checks
    start_health_check_server()

    # Run resilient polling loop
    try:
        asyncio.run(run_bot_polling())
    except KeyboardInterrupt:
        logger.info("Bot execution stopped by user.")
    except Exception as e:
        logger.critical(f"Fatal error in main execution: {e}\n{traceback.format_exc()}")


if __name__ == "__main__":
    main()
