import pytest
import sqlite3
import os
from database.db import DatabaseManager
from database.seed import seed_initial_data

@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_bot.db")

@pytest.fixture
def db(db_path):
    db_mgr = DatabaseManager(db_path)
    db_mgr.init_db()
    return db_mgr

def test_init_db(db_path):
    db_mgr = DatabaseManager(db_path)
    db_mgr.init_db()
    
    # Check tables exist
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert "mail_accounts" in tables
    assert "templates" in tables
    assert "campaigns" in tables
    assert "campaign_leads" in tables

def test_mail_set_crud(db):
    db.add_mail_account("Mail Set 1", "test1@gmail.com", "pass123")
    db.add_mail_account("Mail Set 1", "test2@gmail.com", "pass456")
    db.add_mail_account("Mail Set 2", "test3@gmail.com", "pass789")

    set1 = db.get_mail_set("Mail Set 1")
    assert len(set1) == 2
    assert set1[0]["email"] == "test1@gmail.com"
    assert set1[0]["app_password"] == "pass123"
    assert set1[1]["email"] == "test2@gmail.com"

    all_sets = db.get_all_mail_sets()
    assert "Mail Set 1" in all_sets
    assert "Mail Set 2" in all_sets
    assert len(all_sets["Mail Set 1"]) == 2
    assert len(all_sets["Mail Set 2"]) == 1

def test_template_set_crud(db):
    db.add_template("Template Set 1", "Subject 1 for [Channel Name]", "Body 1 for [Channel Name]")
    db.add_template("Template Set 1", "Subject 2 for [Channel Name]", "Body 2 for [Channel Name]")
    db.add_template("Template Set 2", "Subject 3 for [Channel Name]", "Body 3 for [Channel Name]")

    t_set1 = db.get_template_set("Template Set 1")
    assert len(t_set1) == 2
    assert t_set1[0]["subject"] == "Subject 1 for [Channel Name]"
    assert t_set1[0]["body"] == "Body 1 for [Channel Name]"

    all_t_sets = db.get_all_template_sets()
    assert "Template Set 1" in all_t_sets
    assert "Template Set 2" in all_t_sets
    assert len(all_t_sets["Template Set 1"]) == 2

def test_campaign_and_leads_workflow(db):
    campaign_id = db.create_campaign(
        group_id="-5536170059",
        mail_set_name="Mail Set 1",
        template_set_name="Template Set 1",
        total_leads=3
    )
    assert campaign_id is not None

    leads = [
        {"channel_name": "Channel Alpha", "primary_email": "alpha@example.com"},
        {"channel_name": "Channel Beta", "primary_email": "beta@example.com"},
        {"channel_name": "Channel Gamma", "primary_email": "gamma@example.com"},
    ]
    db.add_campaign_leads(campaign_id, leads)

    pending = db.get_pending_leads(campaign_id)
    assert len(pending) == 3
    assert pending[0]["primary_email"] == "alpha@example.com"
    assert pending[0]["channel_name"] == "Channel Alpha"

    active_campaign = db.get_active_campaign()
    assert active_campaign is not None
    assert active_campaign["id"] == campaign_id
    assert active_campaign["status"] == "active"

    # Update lead status
    db.update_lead_status(
        lead_id=pending[0]["id"],
        status="sent",
        sender_email="salvinaveen478@gmail.com",
        template_used="Subject 1 for Channel Alpha"
    )

    pending_after = db.get_pending_leads(campaign_id)
    assert len(pending_after) == 2

    # Update campaign status
    db.update_campaign_status(campaign_id, "paused")
    assert db.get_active_campaign() is None or db.get_active_campaign()["status"] != "active"

def test_seed_initial_data(db):
    seed_initial_data(db)

    all_mail_sets = db.get_all_mail_sets()
    assert "Mail Set 1" in all_mail_sets
    assert "Mail Set 2" in all_mail_sets
    assert len(all_mail_sets["Mail Set 1"]) == 10
    assert len(all_mail_sets["Mail Set 2"]) == 10

    all_templates = db.get_all_template_sets()
    assert "Template Set 1" in all_templates
    assert "Template Set 2" in all_templates
    assert len(all_templates["Template Set 1"]) == 10
    assert len(all_templates["Template Set 2"]) == 10
