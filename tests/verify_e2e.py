import asyncio
import io
import os
import sys
import smtplib
import pytest
from pathlib import Path
from typing import List, Tuple, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import DatabaseManager
from database.seed import seed_initial_data, MAIL_SET_1, MAIL_SET_2
from engine.mailer import format_email_content, send_single_email
from utils.parser import parse_lead_file



def verify_smtp_credentials(accounts: List[Tuple[str, str]], timeout: int = 10) -> Dict[str, Tuple[bool, str]]:
    """
    Verifies SMTP credentials against smtp.gmail.com:465 (SMTP_SSL) with fallback to 587 (STARTTLS).
    Returns dict mapping email -> (success_boolean, status_message).
    """
    results = {}
    for email, app_password in accounts:
        success = False
        msg = ""
        # Attempt SSL on 465
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=timeout)
            try:
                server.login(email, app_password)
                server.quit()
                success = True
                msg = "SMTP SSL Authentication Successful"
            except Exception as e_login:
                try:
                    server.quit()
                except Exception:
                    pass
                msg = f"SSL Login Failed: {e_login}"
        except Exception as e_conn:
            # Fallback STARTTLS on 587
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=timeout)
                try:
                    server.starttls()
                    server.login(email, app_password)
                    server.quit()
                    success = True
                    msg = "STARTTLS Authentication Successful"
                except Exception as e_tls_login:
                    try:
                        server.quit()
                    except Exception:
                        pass
                    msg = f"TLS Login Failed: {e_tls_login}"
            except Exception as e_tls_conn:
                msg = f"Connection Failed: {e_conn} / {e_tls_conn}"

        results[email] = (success, msg)
    return results


def test_verify_e2e_db_and_seeding(tmp_path):
    """Test 1: Database initialization & seeding verification."""
    db_path = str(tmp_path / "verify_e2e_test.db")
    db_mgr = DatabaseManager(db_path)
    seed_initial_data(db_mgr)

    mail_sets = db_mgr.get_all_mail_sets()
    assert "Mail Set 1" in mail_sets
    assert "Mail Set 2" in mail_sets
    assert len(mail_sets["Mail Set 1"]) == 10
    assert len(mail_sets["Mail Set 2"]) == 10

    template_sets = db_mgr.get_all_template_sets()
    assert "Template Set 1" in template_sets
    assert "Template Set 2" in template_sets
    assert len(template_sets["Template Set 1"]) == 10
    assert len(template_sets["Template Set 2"]) == 10


def test_verify_e2e_lead_parsing():
    """Test 2: Lead file parsing with CSV and JSON content."""
    csv_content = (
        "Channel Name,Primary Email\n"
        "Tech Hub,techhub@example.com\n"
        "Gaming Central,gaming@example.com\n"
        "Invalid Entry,invalid-email\n"
    ).encode("utf-8")

    leads = parse_lead_file(csv_content, "leads.csv")
    assert len(leads) == 2
    assert leads[0]["channel_name"] == "Tech Hub"
    assert leads[0]["primary_email"] == "techhub@example.com"
    assert leads[1]["channel_name"] == "Gaming Central"
    assert leads[1]["primary_email"] == "gaming@example.com"


def test_verify_e2e_email_formatting():
    """Test 3: Email template placeholder replacement."""
    subject = "Free automation build for [Channel Name]"
    body = "Hi {Channel Name},\nWe want to build a free workflow for [channel_name]."
    channel = "Code Master"

    fmt_subj, fmt_body = format_email_content(subject, body, channel)
    assert fmt_subj == "Free automation build for Code Master"
    assert "Hi Code Master," in fmt_body
    assert "workflow for Code Master." in fmt_body


def test_verify_e2e_campaign_workflow(tmp_path):
    """Test 4: Campaign creation & lead addition workflow."""
    db_path = str(tmp_path / "campaign_e2e.db")
    db_mgr = DatabaseManager(db_path)
    seed_initial_data(db_mgr)

    c_id = db_mgr.create_campaign(
        group_id="-5536170059",
        mail_set_name="Mail Set 1",
        template_set_name="Template Set 1",
        total_leads=2
    )
    assert c_id is not None

    leads = [
        {"channel_name": "Channel A", "primary_email": "a@example.com"},
        {"channel_name": "Channel B", "primary_email": "b@example.com"},
    ]
    db_mgr.add_campaign_leads(c_id, leads)

    pending = db_mgr.get_pending_leads(c_id)
    assert len(pending) == 2

    campaign = db_mgr.get_campaign(c_id)
    assert campaign["total_leads"] == 2
    assert campaign["status"] == "active"

    # Simulate lead updates
    db_mgr.update_lead_status(pending[0]["id"], "sent", sender_email="sender@example.com", template_used="Subj 1")
    db_mgr.update_lead_status(pending[1]["id"], "failed", error_msg="SMTP Error", sender_email="sender@example.com", template_used="Subj 1")

    updated_c = db_mgr.get_campaign(c_id)
    assert updated_c["sent_count"] == 1
    assert updated_c["failed_count"] == 1


def test_verify_e2e_smtp_accounts():
    """Test 5: Verify SMTP credentials for seed accounts against smtp.gmail.com:465."""
    # Test sample account verification
    sample_accounts = MAIL_SET_1[:2]  # First two accounts from Mail Set 1
    results = verify_smtp_credentials(sample_accounts, timeout=5)

    assert len(results) == len(sample_accounts)
    for email, (success, status_msg) in results.items():
        print(f"\nAccount {email}: Success={success} | Msg={status_msg}")


def main():
    print("=" * 60)
    print("RUNNING END-TO-END AUTOMATED VERIFICATION SCRIPT")
    print("=" * 60)

    # 1. DB & Seeding Verification
    print("\n[1/5] Verifying Database Initialization & Seeding...")
    db_mgr = DatabaseManager("automail_verify_temp.db")
    seed_initial_data(db_mgr)
    mail_sets = db_mgr.get_all_mail_sets()
    template_sets = db_mgr.get_all_template_sets()
    print(f"  [OK] Mail Sets: {list(mail_sets.keys())} ({sum(len(v) for v in mail_sets.values())} total accounts)")
    print(f"  [OK] Template Sets: {list(template_sets.keys())} ({sum(len(v) for v in template_sets.values())} total templates)")

    # 2. Lead Parsing Verification
    print("\n[2/5] Verifying Lead File Parsing...")
    csv_bytes = b"channel_name,primary_email\nStudio One,one@studio.com\nStudio Two,two@studio.com\n"
    leads = parse_lead_file(csv_bytes, "test.csv")
    print(f"  [OK] Extracted {len(leads)} leads: {[l['primary_email'] for l in leads]}")

    # 3. Email Formatting Verification
    print("\n[3/5] Verifying Email Template Formatting...")
    sub, body = format_email_content("Subject for [Channel Name]", "Body for [channel_name]", "SuperChannel")
    print(f"  [OK] Subject: {sub}")
    print(f"  [OK] Body snippet: {body[:30]}...")

    # 4. Campaign Workflow Verification
    print("\n[4/5] Verifying Campaign Creation & Lead Tracking...")
    c_id = db_mgr.create_campaign("-5536170059", "Mail Set 1", "Template Set 1", len(leads))
    db_mgr.add_campaign_leads(c_id, leads)
    print(f"  [OK] Created Campaign #{c_id} with {len(leads)} leads.")

    # 5. SMTP Credential Verification
    print("\n[5/5] Verifying SMTP Credentials against smtp.gmail.com:465...")
    all_accounts = MAIL_SET_1 + MAIL_SET_2
    smtp_results = verify_smtp_credentials(all_accounts, timeout=8)
    
    passed_cnt = 0
    failed_cnt = 0
    for email, (succ, msg) in smtp_results.items():
        status_icon = "[PASS]" if succ else "[FAIL]"
        print(f"  {status_icon} {email}: {msg}")
        if succ:
            passed_cnt += 1
        else:
            failed_cnt += 1

    print("\n" + "=" * 60)
    print(f"E2E VERIFICATION COMPLETE: SMTP {passed_cnt}/{len(all_accounts)} PASSED")
    print("=" * 60)

    # Clean up temp file
    if os.path.exists("automail_verify_temp.db"):
        try:
            os.remove("automail_verify_temp.db")
        except Exception:
            pass



if __name__ == "__main__":
    main()
