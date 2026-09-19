import asyncio
import random
import smtplib
import socket
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


def send_http_relay_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    subject: str,
    body: str,
    relay_url: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Sends email via HTTP POST over port 443 (HTTPS) to bypass outbound SMTP firewall blocks (Errno 101 on Render).
    Supports HTTP_SMTP_RELAY_URL, RESEND_API_KEY, or SENDGRID_API_KEY.
    """
    import os
    import requests

    target_url = relay_url or os.environ.get("HTTP_SMTP_RELAY_URL") or os.environ.get("HTTP_MAIL_RELAY_URL")
    resend_key = os.environ.get("RESEND_API_KEY")
    sendgrid_key = os.environ.get("SENDGRID_API_KEY")

    if target_url:
        try:
            payload = {
                "sender": sender_email,
                "app_password": app_password,
                "recipient": recipient_email,
                "subject": subject,
                "body": body
            }
            resp = requests.post(target_url, json=payload, timeout=15)
            if resp.status_code in (200, 201, 202):
                return True, "OK (HTTP Relay)"
            else:
                return False, f"HTTP Relay failed ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"HTTP Relay error: {e}"

    elif resend_key:
        try:
            from_name = sender_email.split("@")[0] if "@" in sender_email else "Outreach"
            resp = requests.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {resend_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "from": f"{from_name} <onboarding@resend.dev>",
                    "to": [recipient_email],
                    "reply_to": sender_email,
                    "subject": subject,
                    "text": body
                },
                timeout=15
            )
            if resp.status_code in (200, 201, 202):
                return True, "OK (Resend API HTTPS)"
            else:
                return False, f"Resend API ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"Resend API error: {e}"

    elif sendgrid_key:
        try:
            resp = requests.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {sendgrid_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "personalizations": [{"to": [{"email": recipient_email}]}],
                    "from": {"email": sender_email},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}]
                },
                timeout=15
            )
            if resp.status_code in (200, 201, 202):
                return True, "OK (SendGrid API)"
            else:
                return False, f"SendGrid API failed ({resp.status_code}): {resp.text}"
        except Exception as e:
            return False, f"SendGrid API error: {e}"

    return False, "No HTTP relay URL or API key configured (set HTTP_SMTP_RELAY_URL, RESEND_API_KEY, or SENDGRID_API_KEY)."


def send_single_email(
    sender_email: str,
    app_password: str,
    recipient_email: str,
    subject: str,
    body: str,
    http_relay_url: Optional[str] = None
) -> Tuple[bool, str]:
    """
    Creates proper MIMEText email.
    Connects to smtp.gmail.com over IPv4 (socket.AF_INET) on port 465 (SMTP_SSL) with fallback to 587 (STARTTLS).
    If standard SMTP fails due to cloud network firewall blocks (e.g. [Errno 101] Network is unreachable on Render),
    falls back to sending via HTTP/HTTPS relay on port 443.
    """
    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    # Monkey patch socket.getaddrinfo temporarily to force IPv4 (AF_INET) for SMTP socket resolution
    orig_getaddrinfo = socket.getaddrinfo

    def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        return orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

    socket.getaddrinfo = ipv4_getaddrinfo
    smtp_errors = []

    try:
        # Try IPv4 SMTP_SSL on port 465 first
        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15)
            server.login(sender_email, app_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
            server.quit()
            return True, "OK"
        except Exception as e_ssl:
            smtp_errors.append(f"SSL: {e_ssl}")
            # Fallback to IPv4 STARTTLS on port 587
            try:
                server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
                server.starttls()
                server.login(sender_email, app_password)
                server.sendmail(sender_email, [recipient_email], msg.as_string())
                server.quit()
                return True, "OK"
            except Exception as e_tls:
                smtp_errors.append(f"TLS: {e_tls}")
    finally:
        # Always restore original getaddrinfo
        socket.getaddrinfo = orig_getaddrinfo

    # If standard SMTP calls failed (e.g. [Errno 101] Network unreachable on Render), try HTTP relay fallback over port 443
    http_success, http_msg = send_http_relay_email(
        sender_email, app_password, recipient_email, subject, body, http_relay_url
    )
    if http_success:
        return True, http_msg

    combined_err = " | ".join(smtp_errors)
    return False, f"SMTP failed ({combined_err}). HTTP Relay fallback: {http_msg}"


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
        self.is_running = False
        self.is_paused = False
        self.is_cancelled = False

    def pause(self) -> None:
        """Pause worker dispatch."""
        self.is_paused = True

    def resume(self) -> None:
        """Resume worker dispatch."""
        self.is_paused = False

    def cancel(self) -> None:
        """Cancel worker dispatch."""
        self.is_cancelled = True
        self.is_running = False

    async def start(self) -> None:
        """Executes campaign outreach loop across pending leads."""
        self.is_running = True

        if self.is_cancelled:
            self.db_manager.update_campaign_status(self.campaign_id, "cancelled")
            self.is_running = False
            return

        self.db_manager.update_campaign_status(self.campaign_id, "active")

        campaign = self.db_manager.get_campaign(self.campaign_id)
        if not campaign:
            return

        mail_set_name = campaign["mail_set_name"]
        template_set_name = campaign["template_set_name"]

        all_accounts = self.db_manager.get_mail_set(mail_set_name)
        all_templates = self.db_manager.get_template_set(template_set_name)

        if not all_accounts or not all_templates:
            self.db_manager.update_campaign_status(self.campaign_id, "failed")
            return

        pending_leads = self.db_manager.get_pending_leads(self.campaign_id)
        total_leads = campaign["total_leads"]

        for idx, lead in enumerate(pending_leads, start=1):
            if self.is_cancelled:
                break

            while self.is_paused:
                await asyncio.sleep(1)
                if self.is_cancelled:
                    break

            if self.is_cancelled:
                break

            # Pick random sender account and random template
            account = select_random_account(all_accounts)
            template = random.choice(all_templates)

            channel_name = lead.get("channel_name", "")
            recipient_email = lead.get("primary_email", "")

            formatted_sub, formatted_body = format_email_content(
                template.get("subject", ""),
                template.get("body", ""),
                channel_name
            )

            # Send email
            success, err_msg = send_single_email(
                account["email"],
                account["app_password"],
                recipient_email,
                formatted_sub,
                formatted_body
            )

            status_str = "sent" if success else "failed"
            err_text = None if success else err_msg

            self.db_manager.update_lead_status(
                lead["id"],
                status_str,
                err_text,
                account["email"],
                formatted_sub
            )

            next_delay = random.randint(self.min_delay, self.max_delay)

            if self.progress_callback:
                try:
                    await self.progress_callback(
                        self.campaign_id,
                        idx,
                        total_leads,
                        lead,
                        status_str,
                        err_text,
                        next_delay
                    )
                except Exception as cb_err:
                    pass

            if idx < len(pending_leads) and not self.is_cancelled:
                await asyncio.sleep(next_delay)

        final_status = "cancelled" if self.is_cancelled else "completed"
        self.db_manager.update_campaign_status(self.campaign_id, final_status)
        self.is_running = False
