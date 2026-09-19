import pytest
import asyncio
from unittest.mock import patch, MagicMock
from database.db import DatabaseManager
from engine.mailer import (
    format_email_content,
    select_random_account,
    send_single_email,
    CampaignWorker,
)


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_mailer_bot.db")


@pytest.fixture
def db(db_path):
    db_mgr = DatabaseManager(db_path)
    db_mgr.init_db()
    return db_mgr


# ---------------------------------------------------------------------------
# 1. Tests for format_email_content
# ---------------------------------------------------------------------------
def test_format_email_content_placeholders():
    subj_template = "Sponsorship for [Channel Name] & {channel_name}"
    body_template = "Hi [channel_name], welcome to {Channel Name}!"
    channel_name = "TechZone"

    subj, body = format_email_content(subj_template, body_template, channel_name)

    assert subj == "Sponsorship for TechZone & TechZone"
    assert body == "Hi TechZone, welcome to TechZone!"


def test_format_email_content_none_channel():
    subj_template = "Hello [Channel Name]"
    body_template = "Welcome {channel_name}"

    subj, body = format_email_content(subj_template, body_template, None)

    assert subj == "Hello "
    assert body == "Welcome "


def test_format_email_content_no_placeholders():
    subj, body = format_email_content("General Subject", "General Body", "MyChannel")

    assert subj == "General Subject"
    assert body == "General Body"


# ---------------------------------------------------------------------------
# 2. Tests for select_random_account
# ---------------------------------------------------------------------------
def test_select_random_account_success():
    accounts = [
        {"email": "acc1@gmail.com", "app_password": "p1"},
        {"email": "acc2@gmail.com", "app_password": "p2"},
        {"email": "acc3@gmail.com", "app_password": "p3"},
    ]

    selected = select_random_account(accounts)
    assert selected in accounts


def test_select_random_account_empty():
    with pytest.raises(ValueError, match="No mail accounts available"):
        select_random_account([])


# ---------------------------------------------------------------------------
# 3. Tests for send_single_email
# ---------------------------------------------------------------------------
@patch("smtplib.SMTP_SSL")
def test_send_single_email_ssl_success(mock_smtp_ssl):
    mock_server = MagicMock()
    mock_smtp_ssl.return_value = mock_server

    success, msg = send_single_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body"
    )

    assert success is True
    assert msg == "OK"
    mock_smtp_ssl.assert_called_once_with("smtp.gmail.com", 465, timeout=10)
    mock_server.login.assert_called_once_with("sender@gmail.com", "pass")
    mock_server.sendmail.assert_called_once()
    mock_server.quit.assert_called_once()


@patch("smtplib.SMTP")
@patch("smtplib.SMTP_SSL")
def test_send_single_email_ssl_fail_starttls_success(mock_smtp_ssl, mock_smtp):
    mock_smtp_ssl.side_effect = Exception("SSL port 465 connection failed")

    mock_server_tls = MagicMock()
    mock_smtp.return_value = mock_server_tls

    success, msg = send_single_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body"
    )

    assert success is True
    assert msg == "OK"
    mock_smtp.assert_called_once_with("smtp.gmail.com", 587, timeout=10)
    mock_server_tls.starttls.assert_called_once()
    mock_server_tls.login.assert_called_once_with("sender@gmail.com", "pass")
    mock_server_tls.sendmail.assert_called_once()
    mock_server_tls.quit.assert_called_once()


@patch("smtplib.SMTP")
@patch("smtplib.SMTP_SSL")
def test_send_single_email_all_fail(mock_smtp_ssl, mock_smtp):
    mock_smtp_ssl.side_effect = Exception("SSL Failed")
    mock_smtp.side_effect = Exception("TLS Failed")

    success, msg = send_single_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body"
    )

    assert success is False
    assert "TLS Failed" in msg


@patch("requests.post")
def test_send_http_relay_url_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from engine.mailer import send_http_relay_email
    success, msg = send_http_relay_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body",
        relay_url="https://relay.test.com/send"
    )

    assert success is True
    assert "OK (HTTP Relay)" in msg
    mock_post.assert_called_once()


@patch.dict("os.environ", {"RESEND_API_KEY": "re_test_key"})
@patch("requests.post")
def test_send_http_relay_resend_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    from engine.mailer import send_http_relay_email
    success, msg = send_http_relay_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body"
    )

    assert success is True
    assert "OK (Resend API HTTPS)" in msg
    mock_post.assert_called_once()


@patch.dict("os.environ", {"SENDGRID_API_KEY": "SG.test_key"})
@patch("requests.post")
def test_send_http_relay_sendgrid_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 202
    mock_post.return_value = mock_resp

    from engine.mailer import send_http_relay_email
    success, msg = send_http_relay_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body"
    )

    assert success is True
    assert "OK (SendGrid API)" in msg
    mock_post.assert_called_once()


@patch("smtplib.SMTP")
@patch("smtplib.SMTP_SSL")
@patch("requests.post")
def test_send_single_email_errno_101_fallback(mock_post, mock_smtp_ssl, mock_smtp):
    mock_smtp_ssl.side_effect = OSError(101, "Network is unreachable")
    mock_smtp.side_effect = OSError(101, "Network is unreachable")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_post.return_value = mock_resp

    success, msg = send_single_email(
        sender_email="sender@gmail.com",
        app_password="pass",
        recipient_email="recipient@gmail.com",
        subject="Test Subject",
        body="Test Body",
        http_relay_url="https://relay.test.com/send"
    )

    assert success is True
    assert "OK (HTTP Relay)" in msg
    mock_post.assert_called_once()



# ---------------------------------------------------------------------------
# 4. Tests for CampaignWorker
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
@patch("engine.mailer.send_single_email")
async def test_campaign_worker_execution_flow(mock_send, db):
    mock_send.return_value = (True, "OK")

    # Set up DB data
    db.add_mail_account("Set A", "sender1@gmail.com", "pass1")
    db.add_template("Tpl A", "Hello [Channel Name]", "Body for {channel_name}")

    campaign_id = db.create_campaign("grp1", "Set A", "Tpl A", total_leads=2)
    leads = [
        {"channel_name": "Chan 1", "primary_email": "c1@test.com"},
        {"channel_name": "Chan 2", "primary_email": "c2@test.com"},
    ]
    db.add_campaign_leads(campaign_id, leads)

    callbacks_called = []

    def progress_cb(cid, idx, total, lead, status, err, delay):
        callbacks_called.append((cid, idx, total, status, err, delay))

    worker = CampaignWorker(
        db_manager=db,
        campaign_id=campaign_id,
        progress_callback=progress_cb,
        min_delay=0,
        max_delay=0
    )

    await worker.start()

    # Check database updates
    campaign = db.get_campaign(campaign_id)
    assert campaign["status"] == "completed"

    pending = db.get_pending_leads(campaign_id)
    assert len(pending) == 0

    assert len(callbacks_called) == 2
    assert callbacks_called[0] == (campaign_id, 1, 2, "sent", None, 0)
    assert callbacks_called[1] == (campaign_id, 2, 2, "sent", None, 0)
    assert mock_send.call_count == 2


@pytest.mark.asyncio
@patch("engine.mailer.send_single_email")
async def test_campaign_worker_lead_failure(mock_send, db):
    mock_send.return_value = (False, "SMTP Authentication Failed")

    db.add_mail_account("Set A", "sender1@gmail.com", "pass1")
    db.add_template("Tpl A", "Hello [Channel Name]", "Body for {channel_name}")

    campaign_id = db.create_campaign("grp1", "Set A", "Tpl A", total_leads=1)
    db.add_campaign_leads(campaign_id, [{"channel_name": "Chan 1", "primary_email": "c1@test.com"}])

    callbacks_called = []

    def progress_cb(cid, idx, total, lead, status, err, delay):
        callbacks_called.append((cid, idx, total, status, err, delay))

    worker = CampaignWorker(
        db_manager=db,
        campaign_id=campaign_id,
        progress_callback=progress_cb,
        min_delay=0,
        max_delay=0
    )

    await worker.start()

    campaign = db.get_campaign(campaign_id)
    assert campaign["status"] == "completed"

    assert len(callbacks_called) == 1
    assert callbacks_called[0][3] == "failed"
    assert callbacks_called[0][4] == "SMTP Authentication Failed"


@pytest.mark.asyncio
@patch("engine.mailer.send_single_email")
async def test_campaign_worker_pause_resume(mock_send, db):
    mock_send.return_value = (True, "OK")

    db.add_mail_account("Set A", "sender1@gmail.com", "pass1")
    db.add_template("Tpl A", "Hello [Channel Name]", "Body for {channel_name}")

    campaign_id = db.create_campaign("grp1", "Set A", "Tpl A", total_leads=2)
    db.add_campaign_leads(campaign_id, [
        {"channel_name": "Chan 1", "primary_email": "c1@test.com"},
        {"channel_name": "Chan 2", "primary_email": "c2@test.com"},
    ])

    worker = CampaignWorker(
        db_manager=db,
        campaign_id=campaign_id,
        min_delay=0,
        max_delay=0
    )

    # Pause before start
    worker.pause()
    assert worker.is_paused is True

    # Start in background task
    task = asyncio.create_task(worker.start())
    await asyncio.sleep(0.1)

    # Should still be paused and not completed
    assert task.done() is False

    # Resume worker
    worker.resume()
    assert worker.is_paused is False

    await task

    campaign = db.get_campaign(campaign_id)
    assert campaign["status"] == "completed"


@pytest.mark.asyncio
@patch("engine.mailer.send_single_email")
async def test_campaign_worker_cancellation(mock_send, db):
    mock_send.return_value = (True, "OK")

    db.add_mail_account("Set A", "sender1@gmail.com", "pass1")
    db.add_template("Tpl A", "Hello [Channel Name]", "Body for {channel_name}")

    campaign_id = db.create_campaign("grp1", "Set A", "Tpl A", total_leads=2)
    db.add_campaign_leads(campaign_id, [
        {"channel_name": "Chan 1", "primary_email": "c1@test.com"},
        {"channel_name": "Chan 2", "primary_email": "c2@test.com"},
    ])

    worker = CampaignWorker(
        db_manager=db,
        campaign_id=campaign_id,
        min_delay=0,
        max_delay=0
    )

    worker.cancel()
    assert worker.is_cancelled is True

    await worker.start()

    campaign = db.get_campaign(campaign_id)
    assert campaign["status"] == "cancelled"
