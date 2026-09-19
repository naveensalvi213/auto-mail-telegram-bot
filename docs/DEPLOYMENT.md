# Deployment & SMTP Firewall Bypass Guide

## 🚨 Problem Background: Render Outbound SMTP Blocking

On **Render Free Web Services**, outbound TCP connection attempts to email ports (`25`, `465`, and `587`) are blocked at the container network firewall level to prevent spam abuse. 

When `smtplib` in Python tries to connect to `smtp.gmail.com:465` (SSL) or `smtp.gmail.com:587` (STARTTLS) on Render, the operating system raises:
```text
[Errno 101] Network is unreachable
```

To solve this issue and guarantee **100% 24/7 working outbound email sending**, three deployment and fallback options are available:

---

## 🟢 Option A (Recommended): Free 24/7 Deployment on Koyeb

**Koyeb** ([koyeb.com](https://www.koyeb.com)) is a cloud hosting platform whose free tier **permits outbound SMTP on ports 465 and 587 without a credit card**.

### Automated 1-Click Deployment:
Run the automated Koyeb deployment script:
```bash
python deploy_to_koyeb.py
```

### Steps:
1. Ensure your `.env` contains your `GITHUB_TOKEN`.
2. (Optional) Get a free Koyeb API Token at [koyeb.com/user/settings/api](https://app.koyeb.com/user/settings/api) and set `KOYEB_API_TOKEN=your_token` in `.env`.
3. Running `python deploy_to_koyeb.py` will automatically push the latest code to GitHub and create/update your 24/7 Koyeb worker service!

---

## 🔵 Option B: HTTP-based SMTP Relay Fallback (Port 443 HTTPS)

Outbound HTTPS traffic on port `443` is **never blocked** by Render or any cloud firewall.

`engine/mailer.py` includes built-in fallback to HTTP HTTPS sending whenever standard SMTP ports fail with network error `[Errno 101]`:

### Configuration Options:
Add any of the following environment variables to your cloud dashboard or `.env`:

1. **HTTP SMTP Relay URL:**
   ```env
   HTTP_SMTP_RELAY_URL=https://your-custom-smtp-relay.app/send
   ```
2. **Resend API Key:**
   ```env
   RESEND_API_KEY=re_123456789
   ```
3. **SendGrid API Key:**
   ```env
   SENDGRID_API_KEY=SG.123456789
   ```

When standard SMTP ports (465/587) raise `Errno 101`, `send_single_email()` seamlessly falls back to port 443 HTTPS HTTP relay!

---

## 🟡 Option C: Local 24/7 Execution (Background Daemon)

You can run the bot 24/7 on your local PC or VPS using Python directly:

### Run in Background:
```bash
python main.py
```

### Run with PM2 (Process Manager):
```bash
pm2 start main.py --name auto-mail-bot
```

### Run with Nohup (Linux/VPS):
```bash
nohup python main.py > bot.log 2>&1 &
```

Since local networks and home internet connections do not block outbound SMTP ports 465/587, local execution works 24/7 without restrictions.
