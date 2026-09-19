import pytest
from unittest.mock import MagicMock, AsyncMock
from database.db import DatabaseManager
from bot.handlers import (
    is_authorized_chat,
    set_db_manager,
    id_command,
    addemail_command,
    addtemplate_command,
    listemails_command,
    listtemplates_command,
    status_command,
    pause_command,
    resume_command,
    cancel_command,
    TARGET_GROUP_ID,
)


class DummyChat:
    def __init__(self, chat_id, title="Test Group"):
        self.id = chat_id
        self.title = title


class DummyUser:
    def __init__(self, user_id, is_admin=False):
        self.id = user_id
        self.is_admin = is_admin


class DummyMessage:
    def __init__(self, text=""):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append((text, kwargs))
        return self


class DummyUpdate:
    def __init__(self, chat_id=None, user_id=None, text="", is_admin=False):
        self.effective_chat = DummyChat(chat_id) if chat_id is not None else None
        self.effective_user = DummyUser(user_id, is_admin) if user_id is not None else None
        self.message = DummyMessage(text)
        self.is_admin = is_admin


class DummyContext:
    def __init__(self, args=None, db_mgr=None):
        self.args = args or []
        self.bot_data = {"db_manager": db_mgr} if db_mgr else {}
        self.chat_data = {}


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test_bot_handlers.db")
    db_mgr = DatabaseManager(db_path)
    db_mgr.init_db()
    set_db_manager(db_mgr)
    return db_mgr


def test_is_authorized_chat():
    # Target group match by int or str
    up_target_int = DummyUpdate(chat_id=-5536170059)
    assert is_authorized_chat(up_target_int) is True

    up_target_str = DummyUpdate(chat_id="-5536170059")
    assert is_authorized_chat(up_target_str) is True

    # Unauthorized chat ID
    up_unauth = DummyUpdate(chat_id=123456)
    assert is_authorized_chat(up_unauth) is False

    # Authorized admin user in non-target chat
    up_admin = DummyUpdate(chat_id=123456, user_id=999, is_admin=True)
    assert is_authorized_chat(up_admin) is True

    # None update
    assert is_authorized_chat(None) is False


@pytest.mark.asyncio
async def test_id_command():
    up_target = DummyUpdate(chat_id=-5536170059)
    ctx = DummyContext()
    await id_command(up_target, ctx)

    assert len(up_target.message.replies) == 1
    reply_text, _ = up_target.message.replies[0]
    assert "-5536170059" in reply_text
    assert "YES ✅" in reply_text

    up_other = DummyUpdate(chat_id=999)
    await id_command(up_other, ctx)
    assert len(up_other.message.replies) == 1
    reply_text_other, _ = up_other.message.replies[0]
    assert "NO ❌" in reply_text_other


@pytest.mark.asyncio
async def test_addemail_command_parsing(db):
    up = DummyUpdate(chat_id=-5536170059, text="/addemail Mail Set 1 user@example.com myapppass")
    ctx = DummyContext(args=["Mail", "Set", "1", "user@example.com", "myapppass"], db_mgr=db)

    await addemail_command(up, ctx)

    assert len(up.message.replies) == 1
    assert "user@example.com" in up.message.replies[0][0]

    accounts = db.get_mail_set("Mail Set 1")
    assert len(accounts) == 1
    assert accounts[0]["email"] == "user@example.com"
    assert accounts[0]["app_password"] == "myapppass"


@pytest.mark.asyncio
async def test_addtemplate_command_parsing(db):
    up = DummyUpdate(
        chat_id=-5536170059,
        text='/addtemplate "Template Set 1" Outreach for [Channel Name] | Hello [Channel Name], check this out!'
    )
    ctx = DummyContext(db_mgr=db)

    await addtemplate_command(up, ctx)

    assert len(up.message.replies) == 1
    assert "Template Set 1" in up.message.replies[0][0]

    templates = db.get_template_set("Template Set 1")
    assert len(templates) == 1
    assert templates[0]["subject"] == "Outreach for [Channel Name]"
    assert templates[0]["body"] == "Hello [Channel Name], check this out!"


@pytest.mark.asyncio
async def test_list_commands(db):
    db.add_mail_account("Mail Set 1", "sender1@example.com", "pass1")
    db.add_template("Template Set 1", "Subject 1", "Body 1")

    ctx = DummyContext(db_mgr=db)

    up_emails = DummyUpdate(chat_id=-5536170059)
    await listemails_command(up_emails, ctx)
    assert len(up_emails.message.replies) == 1
    assert "sender1@example.com" in up_emails.message.replies[0][0]

    up_templates = DummyUpdate(chat_id=-5536170059)
    await listtemplates_command(up_templates, ctx)
    assert len(up_templates.message.replies) == 1
    assert "Subject 1" in up_templates.message.replies[0][0]


@pytest.mark.asyncio
async def test_status_and_control_commands(db):
    ctx = DummyContext(db_mgr=db)

    # Status when no campaign
    up_status = DummyUpdate(chat_id=-5536170059)
    await status_command(up_status, ctx)
    assert "No active campaign" in up_status.message.replies[0][0]

    # Create campaign
    c_id = db.create_campaign("-5536170059", "Mail Set 1", "Template Set 1", 5)

    # Status with active campaign
    up_status2 = DummyUpdate(chat_id=-5536170059)
    await status_command(up_status2, ctx)
    assert "ACTIVE" in up_status2.message.replies[0][0]

    # Pause
    up_pause = DummyUpdate(chat_id=-5536170059)
    await pause_command(up_pause, ctx)
    assert f"Campaign #{c_id} has been paused" in up_pause.message.replies[0][0]

    # Resume
    up_resume = DummyUpdate(chat_id=-5536170059)
    await resume_command(up_resume, ctx)
    assert f"Campaign #{c_id} has been resumed" in up_resume.message.replies[0][0]

    # Cancel
    up_cancel = DummyUpdate(chat_id=-5536170059)
    await cancel_command(up_cancel, ctx)
    assert f"Campaign #{c_id} has been cancelled" in up_cancel.message.replies[0][0]
