import os
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from database.db import DatabaseManager
from database.seed import seed_initial_data
from bot.handlers import register_handlers, set_db_manager
from telegram.ext import Application

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk")


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7 OK")

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

    # Instantiate DatabaseManager and seed initial data
    db_manager = DatabaseManager("automail.db")
    seed_initial_data(db_manager)
    set_db_manager(db_manager)

    # Build Telegram Application
    app = Application.builder().token(BOT_TOKEN).build()
    app.bot_data["db_manager"] = db_manager

    # Register handlers
    register_handlers(app)

    logger.info("Starting bot polling...")
    app.run_polling()


if __name__ == "__main__":
    main()
