import logging
from database.db import DatabaseManager
from database.seed import seed_initial_data
from bot.handlers import register_handlers, set_db_manager
from telegram.ext import Application

BOT_TOKEN = "8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk"


def main() -> None:
    # Configure logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )
    logger = logging.getLogger(__name__)
    logger.info("Initializing Auto Mail Telegram Bot...")

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
