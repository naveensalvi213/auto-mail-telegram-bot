import sqlite3
import os
from typing import List, Dict, Optional, Any

class DatabaseManager:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Initialize all required database tables."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Table: mail_accounts
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mail_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_name TEXT NOT NULL,
                email TEXT NOT NULL,
                app_password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Table: templates
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Table: campaigns
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                mail_set_name TEXT NOT NULL,
                template_set_name TEXT NOT NULL,
                total_leads INTEGER NOT NULL DEFAULT 0,
                sent_count INTEGER NOT NULL DEFAULT 0,
                failed_count INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Table: campaign_leads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaign_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id INTEGER NOT NULL,
                channel_name TEXT,
                primary_email TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                error_msg TEXT,
                sender_email TEXT,
                template_used TEXT,
                sent_at TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            );
        """)

        conn.commit()
        conn.close()

    def add_mail_account(self, set_name: str, email: str, app_password: str) -> None:
        """Add a mail sender account to a specific mail set."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO mail_accounts (set_name, email, app_password) VALUES (?, ?, ?);",
            (set_name, email, app_password)
        )
        conn.commit()
        conn.close()

    def get_mail_set(self, set_name: str) -> List[Dict[str, Any]]:
        """Retrieve list of mail accounts for a given set name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, set_name, email, app_password FROM mail_accounts WHERE set_name = ?;",
            (set_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_mail_sets(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve dictionary mapping set_name to list of account dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, set_name, email, app_password FROM mail_accounts ORDER BY set_name, id;")
        rows = cursor.fetchall()
        conn.close()

        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            item = dict(row)
            set_name = item["set_name"]
            if set_name not in result:
                result[set_name] = []
            result[set_name].append(item)
        return result

    def add_template(self, set_name: str, subject: str, body: str) -> None:
        """Add a template to a specific template set."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO templates (set_name, subject, body) VALUES (?, ?, ?);",
            (set_name, subject, body)
        )
        conn.commit()
        conn.close()

    def get_template_set(self, set_name: str) -> List[Dict[str, Any]]:
        """Retrieve list of templates for a given set name."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, set_name, subject, body FROM templates WHERE set_name = ?;",
            (set_name,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_all_template_sets(self) -> Dict[str, List[Dict[str, Any]]]:
        """Retrieve dictionary mapping set_name to list of template dicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, set_name, subject, body FROM templates ORDER BY set_name, id;")
        rows = cursor.fetchall()
        conn.close()

        result: Dict[str, List[Dict[str, Any]]] = {}
        for row in rows:
            item = dict(row)
            set_name = item["set_name"]
            if set_name not in result:
                result[set_name] = []
            result[set_name].append(item)
        return result

    def create_campaign(self, group_id: str, mail_set_name: str, template_set_name: str, total_leads: int) -> int:
        """Create a new campaign and return its campaign_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO campaigns (group_id, mail_set_name, template_set_name, total_leads, status)
               VALUES (?, ?, ?, ?, 'active');""",
            (group_id, mail_set_name, template_set_name, total_leads)
        )
        campaign_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return campaign_id

    def add_campaign_leads(self, campaign_id: int, leads_list: List[Dict[str, Any]]) -> None:
        """Add leads to campaign_leads table."""
        conn = self._get_connection()
        cursor = conn.cursor()
        for lead in leads_list:
            cursor.execute(
                """INSERT INTO campaign_leads (campaign_id, channel_name, primary_email, status)
                   VALUES (?, ?, ?, 'pending');""",
                (campaign_id, lead.get("channel_name"), lead.get("primary_email"))
            )
        conn.commit()
        conn.close()

    def update_lead_status(
        self,
        lead_id: int,
        status: str,
        error_msg: Optional[str] = None,
        sender_email: Optional[str] = None,
        template_used: Optional[str] = None
    ) -> None:
        """Update lead execution status and update campaign metrics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get campaign_id for lead
        cursor.execute("SELECT campaign_id FROM campaign_leads WHERE id = ?;", (lead_id,))
        row = cursor.fetchone()
        campaign_id = row["campaign_id"] if row else None

        cursor.execute(
            """UPDATE campaign_leads
               SET status = ?, error_msg = ?, sender_email = ?, template_used = ?, sent_at = CURRENT_TIMESTAMP
               WHERE id = ?;""",
            (status, error_msg, sender_email, template_used, lead_id)
        )

        if campaign_id:
            if status == "sent":
                cursor.execute(
                    "UPDATE campaigns SET sent_count = sent_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (campaign_id,)
                )
            elif status == "failed":
                cursor.execute(
                    "UPDATE campaigns SET failed_count = failed_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (campaign_id,)
                )

        conn.commit()
        conn.close()

    def get_pending_leads(self, campaign_id: int) -> List[Dict[str, Any]]:
        """Retrieve all pending leads for a given campaign."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, campaign_id, channel_name, primary_email, status
               FROM campaign_leads
               WHERE campaign_id = ? AND status = 'pending'
               ORDER BY id;""",
            (campaign_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_campaign(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a specific campaign by campaign_id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, group_id, mail_set_name, template_set_name, total_leads, sent_count, failed_count, status, created_at, updated_at
               FROM campaigns
               WHERE id = ?;""",
            (campaign_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_active_campaign(self) -> Optional[Dict[str, Any]]:
        """Retrieve the currently active campaign if one exists."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT id, group_id, mail_set_name, template_set_name, total_leads, sent_count, failed_count, status, created_at, updated_at
               FROM campaigns
               WHERE status = 'active'
               ORDER BY id DESC LIMIT 1;"""
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def update_campaign_status(self, campaign_id: int, status: str) -> None:
        """Update campaign status ('active', 'paused', 'completed', 'cancelled')."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE campaigns SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
            (status, campaign_id)
        )
        conn.commit()
        conn.close()
