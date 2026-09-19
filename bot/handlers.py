import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from database.db import DatabaseManager
from engine.mailer import CampaignWorker
from utils.parser import parse_lead_file

logger = logging.getLogger(__name__)

TARGET_GROUP_ID = "-5536170059"

_global_db_manager: Optional[DatabaseManager] = None
ACTIVE_WORKERS: Dict[int, CampaignWorker] = {}


def get_db_manager(context: Optional[ContextTypes.DEFAULT_TYPE] = None) -> DatabaseManager:
    """Retrieve DatabaseManager instance from context or fallback global."""
    global _global_db_manager
    if context and hasattr(context, "bot_data") and "db_manager" in context.bot_data:
        return context.bot_data["db_manager"]
    if _global_db_manager is None:
        _global_db_manager = DatabaseManager("automail.db")
        _global_db_manager.init_db()
    return _global_db_manager


def set_db_manager(db_mgr: DatabaseManager) -> None:
    """Set the global DatabaseManager instance (useful for testing)."""
    global _global_db_manager
    _global_db_manager = db_mgr


def is_authorized_chat(update: Any) -> bool:
    """
    Ensures lead uploads and campaign management occur in group -5536170059, private chat, or authorized admin.
    """
    if not update:
        return False

    chat = getattr(update, "effective_chat", None)
    if chat:
        chat_id_str = str(chat.id)
        chat_type = getattr(chat, "type", "unknown")
        logger.info(f"Incoming update from chat_id: {chat_id_str} (Type: {chat_type})")
        if chat_id_str == TARGET_GROUP_ID or chat_id_str.endswith("5536170059") or chat_type == "private":
            return True
        if getattr(chat, "is_admin", False):
            return True

    user = getattr(update, "effective_user", None)
    if user and getattr(user, "is_admin", False):
        return True

    return False


async def start_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /start & /help: Display welcome guide and bot capabilities."""
    welcome_text = (
        "🤖 **Auto Mail Telegram Bot**\n\n"
        "Welcome! I am an automated email dispatch bot built for managing email outreach campaigns.\n\n"
        "📋 **Capabilities:**\n"
        "• 📄 **Lead File Parsing:** Upload `.csv`, `.xlsx`, or `.json` files to extract target emails and channel names.\n"
        "• 📧 **Mail Sets & Templates:** Select custom sender account pools and email templates.\n"
        "• 🚀 **Campaign Execution:** Background email sending with random sender rotation and delays.\n"
        "• 📊 **Live Progress & Control:** Pause, resume, cancel, and check real-time progress.\n\n"
        "🛠️ **Available Commands:**\n"
        "• `/id` or `/groupid` - Check current Chat/Group ID and authorization.\n"
        "• `/addemail <set_name> <email> <app_password>` - Add a sender email account.\n"
        "• `/addtemplate <set_name> <subject> | <body>` - Add an email template.\n"
        "• `/listemails` - View all configured mail sets and accounts.\n"
        "• `/listtemplates` - View all configured template sets.\n"
        "• `/status` - Check active campaign progress.\n"
        "• `/pause` - Pause active campaign.\n"
        "• `/resume` - Resume paused campaign.\n"
        "• `/cancel` - Cancel active campaign.\n\n"
        "🔒 *Note:* Lead uploads and campaign operations are restricted to Group `-5536170059`."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /id or /groupid: Respond with chat/group ID and target group match status."""
    if not update.effective_chat:
        return
    chat_id = str(update.effective_chat.id)
    chat_title = getattr(update.effective_chat, "title", "Private Chat")
    matches = chat_id == TARGET_GROUP_ID
    status = "YES ✅ (Authorized)" if matches else f"NO ❌ (Target: `{TARGET_GROUP_ID}`)"

    reply_text = (
        f"🆔 **Chat / Group Information**\n\n"
        f"• **Title:** {chat_title}\n"
        f"• **Chat ID:** `{chat_id}`\n"
        f"• **Target Group Match:** {status}"
    )
    await update.message.reply_text(reply_text, parse_mode="Markdown")


async def document_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Document upload handler:
    Checks file extension (.xlsx, .csv, .json), downloads bytes, calls parse_lead_file,
    stores parsed leads in temporary active context, replies with summary & Mail Set inline keyboard.
    """
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat! Lead file uploads are restricted to target group `-5536170059`.", parse_mode="Markdown")
        return

    doc = update.message.document
    if not doc or not doc.file_name:
        return

    ext = Path(doc.file_name).suffix.lower()
    if ext not in [".xlsx", ".xls", ".csv", ".json"]:
        await update.message.reply_text("⚠️ Invalid file format! Please upload a `.xlsx`, `.csv`, or `.json` lead file.", parse_mode="Markdown")
        return

    file = await doc.get_file()
    byte_array = await file.download_as_bytearray()
    file_bytes = bytes(byte_array)

    try:
        leads = parse_lead_file(file_bytes, doc.file_name)
    except Exception as e:
        logger.error(f"Error parsing lead file: {e}")
        await update.message.reply_text(f"❌ Failed to parse lead file: {e}")
        return

    if not leads:
        await update.message.reply_text("⚠️ No valid leads extracted from the file. Please check file contents and try again.")
        return

    # Store leads and file info in chat_data session
    context.chat_data["pending_leads"] = leads
    context.chat_data["lead_filename"] = doc.file_name

    db_mgr = get_db_manager(context)
    all_mail_sets = db_mgr.get_all_mail_sets()

    keyboard = []
    if all_mail_sets:
        for set_name in all_mail_sets.keys():
            keyboard.append([InlineKeyboardButton(f"[ {set_name} ]", callback_data=f"mail_set:{set_name}")])
    else:
        keyboard.append([InlineKeyboardButton("[ Mail Set 1 ]", callback_data="mail_set:Mail Set 1")])
        keyboard.append([InlineKeyboardButton("[ Mail Set 2 ]", callback_data="mail_set:Mail Set 2")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    summary_text = f"📊 Lead File Received! Total extracted: {len(leads)} leads.\n\nPlease select a Mail Set:"
    await update.message.reply_text(summary_text, reply_markup=reply_markup)


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback Query Handlers for Mail Set selection, Template Set selection, and Start Campaign."""
    query = update.callback_query
    if not query:
        return

    data = query.data or ""
    db_mgr = get_db_manager(context)

    if data.startswith("mail_set:"):
        await query.answer()
        mail_set_name = data.split("mail_set:", 1)[1]
        context.chat_data["selected_mail_set"] = mail_set_name

        all_template_sets = db_mgr.get_all_template_sets()
        keyboard = []
        if all_template_sets:
            for t_set in all_template_sets.keys():
                keyboard.append([InlineKeyboardButton(f"[ {t_set} ]", callback_data=f"template_set:{t_set}")])
        else:
            keyboard.append([InlineKeyboardButton("[ Template Set 1 ]", callback_data="template_set:Template Set 1")])
            keyboard.append([InlineKeyboardButton("[ Template Set 2 ]", callback_data="template_set:Template Set 2")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"📧 Selected Mail Set: **{mail_set_name}**\n\nNow select a Template Set:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif data.startswith("template_set:"):
        await query.answer()
        template_set_name = data.split("template_set:", 1)[1]
        context.chat_data["selected_template_set"] = template_set_name

        mail_set_name = context.chat_data.get("selected_mail_set", "N/A")
        leads = context.chat_data.get("pending_leads", [])

        keyboard = [[InlineKeyboardButton("[ 🚀 Start Campaign ]", callback_data="start_campaign")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            f"📧 Selected Mail Set: **{mail_set_name}**\n"
            f"📝 Selected Template Set: **{template_set_name}**\n"
            f"📊 Total Extracted Leads: **{len(leads)}**\n\n"
            f"Click below to launch the outreach campaign!",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    elif data == "start_campaign":
        await query.answer()
        leads = context.chat_data.get("pending_leads")
        mail_set_name = context.chat_data.get("selected_mail_set")
        template_set_name = context.chat_data.get("selected_template_set")

        if not leads or not mail_set_name or not template_set_name:
            await query.edit_message_text("⚠️ Session expired or missing selection data. Please upload the lead file again.")
            return

        chat_id = str(update.effective_chat.id)
        campaign_id = db_mgr.create_campaign(chat_id, mail_set_name, template_set_name, len(leads))
        db_mgr.add_campaign_leads(campaign_id, leads)

        status_msg = await query.edit_message_text(
            f"🚀 **Campaign #{campaign_id} Initialized!**\n"
            f"• Mail Set: `{mail_set_name}`\n"
            f"• Template Set: `{template_set_name}`\n"
            f"• Leads: `{len(leads)}`\n"
            f"Starting dispatch...",
            parse_mode="Markdown"
        )

        async def progress_callback(
            c_id: int,
            lead_index: int,
            total_leads: int,
            lead: Dict[str, Any],
            status: str,
            error_msg: Optional[str],
            next_delay: int
        ) -> None:
            icon = "✅" if status == "sent" else "❌"
            err_info = f"\nError: `{error_msg}`" if error_msg else ""
            msg_text = (
                f"📊 **Campaign #{c_id} Progress** ({lead_index}/{total_leads})\n"
                f"• Status: {icon} **{status.upper()}**\n"
                f"• Recipient: `{lead.get('primary_email')}`\n"
                f"• Channel: `{lead.get('channel_name')}`{err_info}\n"
                f"• Next delay: `{next_delay}s`"
            )
            try:
                if status_msg:
                    await status_msg.edit_text(msg_text, parse_mode="Markdown")
            except Exception as e:
                logger.debug(f"Could not update status message: {e}")

        # Set min_delay/max_delay to small values for bot execution or defaults
        worker = CampaignWorker(
            db_manager=db_mgr,
            campaign_id=campaign_id,
            progress_callback=progress_callback,
            min_delay=2,
            max_delay=5
        )
        ACTIVE_WORKERS[campaign_id] = worker
        if context.bot_data is not None:
            context.bot_data["active_worker"] = worker
            context.bot_data["active_campaign_id"] = campaign_id

        asyncio.create_task(worker.start())

        # Clear pending leads from chat session
        context.chat_data.pop("pending_leads", None)


async def addemail_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /addemail <set_name> <email> <app_password>: Adds email account to database mail set."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    args = context.args or []
    if len(args) < 3:
        await update.message.reply_text("⚠️ Usage: `/addemail <set_name> <email> <app_password>`\nExample: `/addemail Mail Set 1 test@gmail.com apppass123`", parse_mode="Markdown")
        return

    app_password = args[-1]
    email = args[-2]
    set_name = " ".join(args[:-2]).strip('"').strip("'")

    db_mgr = get_db_manager(context)
    db_mgr.add_mail_account(set_name, email, app_password)

    await update.message.reply_text(f"✅ Sender email `{email}` successfully added to `{set_name}`.", parse_mode="Markdown")


async def addtemplate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /addtemplate <set_name> <subject> | <body>: Adds template to database template set."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    text = update.message.text or ""
    # Extract text after command name
    parts = text.split(maxsplit=1)
    if len(parts) < 2 or "|" not in parts[1]:
        await update.message.reply_text(
            "⚠️ Usage: `/addtemplate <set_name> <subject> | <body>`\n"
            "Example: `/addtemplate Template Set 1 Outreach for [Channel Name] | Hey [Channel Name], ...`",
            parse_mode="Markdown"
        )
        return

    raw_args = parts[1]
    left, body = raw_args.split("|", 1)
    left = left.strip()
    body = body.strip()

    db_mgr = get_db_manager(context)
    existing_sets = db_mgr.get_all_template_sets()

    set_name = None
    subject = None

    # Check if left starts with quotes e.g. "Template Set 1" Subject
    if left.startswith('"') and '"' in left[1:]:
        set_name, subject = left[1:].split('"', 1)
        set_name = set_name.strip()
        subject = subject.strip()
    elif left.startswith("'") and "'" in left[1:]:
        set_name, subject = left[1:].split("'", 1)
        set_name = set_name.strip()
        subject = subject.strip()
    else:
        # Check against existing set names
        for existing in existing_sets.keys():
            if left.lower().startswith(existing.lower()):
                set_name = existing
                subject = left[len(existing):].strip()
                break

    if not set_name or not subject:
        tokens = left.split()
        if len(tokens) >= 3 and tokens[0].lower() == "template" and tokens[1].lower() == "set":
            set_name = f"{tokens[0]} {tokens[1]} {tokens[2]}"
            subject = " ".join(tokens[3:])
        elif len(tokens) >= 2:
            set_name = tokens[0]
            subject = " ".join(tokens[1:])
        else:
            set_name = "Template Set 1"
            subject = left

    if not subject:
        subject = "Default Subject"

    db_mgr.add_template(set_name, subject, body)
    await update.message.reply_text(
        f"✅ Template added to `{set_name}`!\n• **Subject:** {subject}",
        parse_mode="Markdown"
    )


async def listemails_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /listemails: Lists all mail sets and sender accounts in database."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    all_sets = db_mgr.get_all_mail_sets()

    if not all_sets:
        await update.message.reply_text("📧 No mail sets configured in database.")
        return

    msg_lines = ["📧 **Configured Mail Sets:**\n"]
    for set_name, accounts in all_sets.items():
        msg_lines.append(f"• **{set_name}** ({len(accounts)} accounts):")
        for acc in accounts:
            msg_lines.append(f"  - `{acc['email']}`")
        msg_lines.append("")

    await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")


async def listtemplates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /listtemplates: Lists all template sets and subjects in database."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    all_sets = db_mgr.get_all_template_sets()

    if not all_sets:
        await update.message.reply_text("📝 No template sets configured in database.")
        return

    msg_lines = ["📝 **Configured Template Sets:**\n"]
    for set_name, templates in all_sets.items():
        msg_lines.append(f"• **{set_name}** ({len(templates)} templates):")
        for t in templates:
            msg_lines.append(f"  - `{t['subject']}`")
        msg_lines.append("")

    await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /status: Displays active campaign progress."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    campaign = db_mgr.get_active_campaign()

    if not campaign:
        await update.message.reply_text("ℹ️ No active campaign currently running.")
        return

    total = campaign["total_leads"]
    sent = campaign["sent_count"]
    failed = campaign["failed_count"]
    remaining = max(0, total - sent - failed)

    status_text = (
        f"📊 **Active Campaign Status** (ID #{campaign['id']})\n\n"
        f"• **Status:** `{campaign['status'].upper()}`\n"
        f"• **Mail Set:** `{campaign['mail_set_name']}`\n"
        f"• **Template Set:** `{campaign['template_set_name']}`\n"
        f"• **Total Leads:** `{total}`\n"
        f"• **Sent:** `{sent}` | **Failed:** `{failed}` | **Remaining:** `{remaining}`"
    )
    await update.message.reply_text(status_text, parse_mode="Markdown")


async def pause_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /pause: Calls active worker pause() and updates DB."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    campaign = db_mgr.get_active_campaign()

    if not campaign:
        await update.message.reply_text("ℹ️ No active campaign found to pause.")
        return

    campaign_id = campaign["id"]
    worker = ACTIVE_WORKERS.get(campaign_id) or (context.bot_data.get("active_worker") if context.bot_data else None)

    if worker:
        worker.pause()
    db_mgr.update_campaign_status(campaign_id, "paused")

    await update.message.reply_text(f"⏸️ Campaign #{campaign_id} has been paused.", parse_mode="Markdown")


async def resume_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /resume: Calls active worker resume() and updates DB."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    # Check for paused or active campaign
    campaign = db_mgr.get_active_campaign()
    if not campaign:
        conn = db_mgr._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_id, mail_set_name, template_set_name, total_leads, sent_count, failed_count, status FROM campaigns WHERE status = 'paused' ORDER BY id DESC LIMIT 1;")
        row = cursor.fetchone()
        conn.close()
        campaign = dict(row) if row else None

    if not campaign:
        await update.message.reply_text("ℹ️ No paused campaign found to resume.")
        return

    campaign_id = campaign["id"]
    worker = ACTIVE_WORKERS.get(campaign_id) or (context.bot_data.get("active_worker") if context.bot_data else None)

    if worker:
        worker.resume()
    db_mgr.update_campaign_status(campaign_id, "active")

    await update.message.reply_text(f"▶️ Campaign #{campaign_id} has been resumed.", parse_mode="Markdown")


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Command /cancel: Calls active worker cancel() and updates DB."""
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Unauthorized chat.")
        return

    db_mgr = get_db_manager(context)
    campaign = db_mgr.get_active_campaign()

    if not campaign:
        conn = db_mgr._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_id, mail_set_name, template_set_name, total_leads, sent_count, failed_count, status FROM campaigns WHERE status IN ('active', 'paused') ORDER BY id DESC LIMIT 1;")
        row = cursor.fetchone()
        conn.close()
        campaign = dict(row) if row else None

    if not campaign:
        await update.message.reply_text("ℹ️ No active/paused campaign found to cancel.")
        return

    campaign_id = campaign["id"]
    worker = ACTIVE_WORKERS.get(campaign_id) or (context.bot_data.get("active_worker") if context.bot_data else None)

    if worker:
        worker.cancel()
    db_mgr.update_campaign_status(campaign_id, "cancelled")

    await update.message.reply_text(f"🛑 Campaign #{campaign_id} has been cancelled.", parse_mode="Markdown")


def register_handlers(app: Application) -> None:
    """Registers all command, message, and callback handlers to the PTB Application."""
    app.add_handler(CommandHandler(["start", "help"], start_help_command))
    app.add_handler(CommandHandler(["id", "groupid"], id_command))
    app.add_handler(CommandHandler("addemail", addemail_command))
    app.add_handler(CommandHandler("addtemplate", addtemplate_command))
    app.add_handler(CommandHandler("listemails", listemails_command))
    app.add_handler(CommandHandler("listtemplates", listtemplates_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("pause", pause_command))
    app.add_handler(CommandHandler("resume", resume_command))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(MessageHandler(filters.Document.ALL, document_handler))
    app.add_handler(CallbackQueryHandler(callback_query_handler))
