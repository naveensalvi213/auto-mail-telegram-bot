# Auto Mail Telegram Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Telegram bot for automated outreach that parses lead files (`.xlsx`, `.csv`, `.json`), allows selecting pre-configured/custom mail sender sets and template sets, and sends outreach emails with 20–60s randomized delays and sender account rotation in Telegram group `-5536170059`.

**Architecture:** Python application with `python-telegram-bot` (v20+ async) for Telegram handling, SQLite for data persistence, `pandas`/`openpyxl` for lead extraction, and `aiosmtplib`/`smtplib` for SMTP account rotation & deliverability.

**Tech Stack:** Python 3.10+, `python-telegram-bot`, `pandas`, `openpyxl`, `sqlite3`, `pytest`.

## Global Constraints
- Target Group ID: `-5536170059`
- Telegram Bot Token: `8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk`
- Delays between emails: `random.randint(20, 60)` seconds
- Sender rotation: Randomly pick active email account from selected Mail Set for each lead email.

---

### Task 1: Environment Setup & Database Layer

**Files:**
- Create: `requirements.txt`
- Create: `database/db.py`
- Create: `database/seed.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: None
- Produces: `init_db()`, `add_mail_account()`, `get_mail_set()`, `add_template()`, `get_template_set()`, `create_campaign()`, `update_lead_status()`, `seed_initial_data()`

- [ ] **Step 1: Create `requirements.txt`**
```text
python-telegram-bot==20.8
pandas==2.2.0
openpyxl==3.1.2
pytest==8.0.0
pytest-asyncio==0.23.5
```

- [ ] **Step 2: Write failing test `tests/test_db.py` for database CRUD operations**
```python
import pytest
import sqlite3
import os
from database.db import DatabaseManager

@pytest.fixture
def db():
    db_path = "test_bot.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    db_mgr = DatabaseManager(db_path)
    db_mgr.init_db()
    yield db_mgr
    if os.path.exists(db_path):
        os.remove(db_path)

def test_mail_set_and_template_crud(db):
    db.add_mail_account("Set 1", "test@gmail.com", "app_pass_123")
    accounts = db.get_mail_set("Set 1")
    assert len(accounts) == 1
    assert accounts[0]["email"] == "test@gmail.com"

    db.add_template("Set 1", "Subject 1", "Body 1 with [Channel Name]")
    templates = db.get_template_set("Set 1")
    assert len(templates) == 1
    assert templates[0]["subject"] == "Subject 1"
```

- [ ] **Step 3: Run test to verify it fails**
Run: `pytest tests/test_db.py` (expected failure as `database.db` does not exist yet)

- [ ] **Step 4: Implement `database/db.py` and `database/seed.py`**
Implement database schema (`mail_accounts`, `templates`, `campaigns`, `campaign_leads`) and pre-seed Mail Set 1 (10 emails), Mail Set 2 (10 emails), Template Set 1 (10 templates), and Template Set 2 (10 variation templates).

- [ ] **Step 5: Run tests to verify they pass**
Run: `pytest tests/test_db.py` (expected PASS)

- [ ] **Step 6: Commit**
`git add requirements.txt database/ tests/ && git commit -m "feat: setup database layer and seeding"`

---

### Task 2: Lead File Parser Engine

**Files:**
- Create: `utils/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: Raw file bytes or file paths (`.csv`, `.xlsx`, `.json`)
- Produces: `parse_lead_file(file_path_or_bytes, filename) -> list[dict]` where each dict has `channel_name` and `primary_email`.

- [ ] **Step 1: Write failing test `tests/test_parser.py`**
```python
import pytest
from utils.parser import parse_lead_file
import pandas as pd
import json

def test_parse_csv(tmp_path):
    csv_file = tmp_path / "leads.csv"
    csv_file.write_text("Channel Name,Primary Email\nTechChannel,tech@example.com\nDesignHub,info@design.com")
    leads = parse_lead_file(str(csv_file))
    assert len(leads) == 2
    assert leads[0]["channel_name"] == "TechChannel"
    assert leads[0]["primary_email"] == "tech@example.com"
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_parser.py`

- [ ] **Step 3: Implement `utils/parser.py`**
Implement flexible column matching for `Channel Name` / `channel_name` / `Channel` and `Primary Email` / `email`, plus standard email format validation.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_parser.py`

- [ ] **Step 5: Commit**
`git add utils/ tests/test_parser.py && git commit -m "feat: add lead document parser for xlsx csv json"`

---

### Task 3: Email Outreach Dispatch Engine

**Files:**
- Create: `engine/mailer.py`
- Test: `tests/test_mailer.py`

**Interfaces:**
- Consumes: DatabaseManager, Campaign parameters
- Produces: `send_single_email(sender_email, app_password, recipient_email, subject, body)`, `CampaignWorker` class for managing campaign lifecycle (start, pause, resume, cancel) with 20–60s random delay and account rotation.

- [ ] **Step 1: Write failing test `tests/test_mailer.py`**
```python
import pytest
from engine.mailer import format_email_content, select_random_account

def test_format_email_content():
    template_sub = "Free system for [Channel Name]"
    template_body = "Hey [Channel Name],\nLet us build AI for you."
    sub, body = format_email_content(template_sub, template_body, "Awesome Studio")
    assert sub == "Free system for Awesome Studio"
    assert "Hey Awesome Studio" in body

def test_select_random_account():
    accounts = [
        {"email": "a@gmail.com", "app_password": "passa"},
        {"email": "b@gmail.com", "app_password": "passb"}
    ]
    acc = select_random_account(accounts)
    assert acc["email"] in ["a@gmail.com", "b@gmail.com"]
```

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_mailer.py`

- [ ] **Step 3: Implement `engine/mailer.py`**
Implement subject/body placeholder replacement, account rotation, MIME message generation, SMTP sending with fallback, and campaign worker loop with `random.randint(20, 60)` delay.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_mailer.py`

- [ ] **Step 5: Commit**
`git add engine/ tests/test_mailer.py && git commit -m "feat: implement mailer outreach engine with rotation and random delay"`

---

### Task 4: Telegram Bot Handlers & UI Workflow

**Files:**
- Create: `bot/handlers.py`
- Create: `main.py`
- Test: `tests/test_bot_handlers.py`

**Interfaces:**
- Consumes: DatabaseManager, CampaignWorker, Telegram Bot Token (`8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk`), Group ID (`-5536170059`)
- Produces: Bot application runner with command handlers (`/start`, `/id`, `/addemail`, `/addtemplate`, `/listemails`, `/listtemplates`, `/status`, `/pause`, `/resume`, `/cancel`), file handler for lead documents, and inline callback handlers.

- [ ] **Step 1: Write tests for bot handler helper functions in `tests/test_bot_handlers.py`**
Test command parsing, group ID restriction filter, and command helper responses.

- [ ] **Step 2: Run test to verify it fails**
Run: `pytest tests/test_bot_handlers.py`

- [ ] **Step 3: Implement `bot/handlers.py` and `main.py`**
Implement group security check, document handling flow, inline keyboard set pickers, progress updates to Telegram group `-5536170059`, and live status display.

- [ ] **Step 4: Run test to verify it passes**
Run: `pytest tests/test_bot_handlers.py`

- [ ] **Step 5: Commit**
`git add bot/ main.py tests/test_bot_handlers.py && git commit -m "feat: implement telegram bot handlers and main entrypoint"`

---

### Task 5: End-to-End Verification & SMTP Connectivity Testing

**Files:**
- Modify/Execute: End-to-end verification script `tests/verify_e2e.py`

**Interfaces:**
- Validates:
  1. Database initial seeding (20 emails, 20 templates).
  2. Parse lead file (including sample `.xlsx` or `.csv`).
  3. Verify SMTP credentials against Gmail servers.
  4. Bot startup & Telegram listener.

- [ ] **Step 1: Write E2E verification test `tests/verify_e2e.py`**
- [ ] **Step 2: Run E2E test suite**
- [ ] **Step 3: Verify all test outputs and present live bot status**
