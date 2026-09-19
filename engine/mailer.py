import asyncio
import random
import smtplib
from email.mime.text import MIMEText
from typing import List, Dict, Tuple, Optional, Callable, Any

def format_email_content(template_subject: str, template_body: str, channel_name: str) -> Tuple[str, str]:
    """
    Replaces placeholders [Channel Name], [channel_name], {Channel Name}, {channel_name} with channel_name.
    """
    ch_name = channel_name if channel_name is not None else ""
    placeholders = ["[Channel Name]", "[channel_name]", "{Channel Name}", "{channel_name}"]

    formatted_subject = template_subject or ""
    formatted_body = template_body or ""

    for ph in placeholders:
        formatted_subject = formatted_subject.replace(ph, ch_name)
        formatted_body = formatted_body.replace(ph, ch_name)

    return formatted_subject, formatted_body


def select_random_account(accounts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Randomly selects one sender account from the provided mail set list.
    """
    if not accounts:
        raise ValueError("No mail accounts available in set")
    return random.choice(accounts)


def send_single_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    subject: str,
    body: str
) -> Tuple[bool, str]:
    """
    Creates proper MIMEText email.
    Connects to smtp.gmail.com on port 465 (SMTP_SSL) with fallback to 587 (STARTTLS).
    Authenticates using sender_email and app_password.
    Sends email to recipient_email and closes connection cleanly.
    Catches exceptions and returns (True, "OK") or (False, str(e)).
    """
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Try SMTP_SSL on port 465 first
    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
        try:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
            server.quit()
            return True, "OK"
        except Exception as e_ssl_inner:
            try:
                server.quit()
            except Exception:
                pass
            raise e_ssl_inner
    except Exception:
        # Fallback to STARTTLS on port 587
        try:
            server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
            try:
                server.starttls()
                server.login(sender_email, app_password)
                server.sendmail(sender_email, [recipient_email], msg.as_string())
                server.quit()
                return True, "OK"
            except Exception as e_tls_inner:
                try:
                    server.quit()
                except Exception:
                    pass
                return False, str(e_tls_inner)
        except Exception as e_fallback:
            return False, str(e_fallback)


class CampaignWorker:
    def __init__(
        self,
        db_manager: Any,
        campaign_id: int,
        progress_callback: Optional[Callable] = None,
        min_delay: int = 20,
        max_delay: int = 60
    ):
        self.db_manager = db_manager
        self.campaign_id = campaign_id
        self.progress_callback = progress_callback
        self.min_delay = min_delay
        self.max_delay = max_delay

        self.is_running: bool = False
        self.is_paused: bool = False
        self.is_cancelled: bool = False

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def cancel(self) -> None:
        self.is_cancelled = True
        self.is_paused = False

    async def start(self) -> None:
        self.is_running = True

        try:
            campaign = self.db_manager.get_campaign(self.campaign_id)
            if not campaign:
                return

            mail_set_name = campaign["mail_set_name"]
            template_set_name = campaign["template_set_name"]

            accounts = self.db_manager.get_mail_set(mail_set_name)
            templates = self.db_manager.get_template_set(template_set_name)
            pending_leads = self.db_manager.get_pending_leads(self.campaign_id)

            total_leads = len(pending_leads)

            for lead_index, lead in enumerate(pending_leads, start=1):
                if self.is_cancelled:
                    break

                while self.is_paused:
                    if self.is_cancelled:
                        break
                    await asyncio.sleep(0.1)

                if self.is_cancelled:
                    break

                if not accounts:
                    status = "failed"
                    error_msg = "No mail accounts available in set"
                    sender_email = None
                    formatted_subject = None
                elif not templates:
                    status = "failed"
                    error_msg = "No templates available in set"
                    sender_email = None
                    formatted_subject = None
                else:
                    account = select_random_account(accounts)
                    template = random.choice(templates)
                    sender_email = account["email"]

                    channel_name = lead.get("channel_name") or ""
                    formatted_subject, formatted_body = format_email_content(
                        template["subject"],
                        template["body"],
                        channel_name
                    )

                    success, err_res = send_single_email(
                        sender_email=account["email"],
                        app_password=account["app_password"],
                        recipient_email=lead["primary_email"],
                        subject=formatted_subject,
                        body=formatted_body
                    )

                    if success:
                        status = "sent"
                        error_msg = None
                    else:
                        status = "failed"
                        error_msg = err_res

                self.db_manager.update_lead_status(
                    lead_id=lead["id"],
                    status=status,
                    error_msg=error_msg,
                    sender_email=sender_email,
                    template_used=formatted_subject
                )

                if self.min_delay > 0 or self.max_delay > 0:
                    low = min(self.min_delay, self.max_delay)
                    high = max(self.min_delay, self.max_delay)
                    next_delay = random.randint(low, high)
                else:
                    next_delay = 0

                if self.progress_callback:
                    if asyncio.iscoroutinefunction(self.progress_callback):
                        await self.progress_callback(
                            self.campaign_id,
                            lead_index,
                            total_leads,
                            lead,
                            status,
                            error_msg,
                            next_delay
                        )
                    else:
                        self.progress_callback(
                            self.campaign_id,
                            lead_index,
                            total_leads,
                            lead,
                            status,
                            error_msg,
                            next_delay
                        )

                if next_delay > 0 and not self.is_cancelled:
                    await asyncio.sleep(next_delay)

            if self.is_cancelled:
                self.db_manager.update_campaign_status(self.campaign_id, "cancelled")
            else:
                self.db_manager.update_campaign_status(self.campaign_id, "completed")

        finally:
            self.is_running = False
