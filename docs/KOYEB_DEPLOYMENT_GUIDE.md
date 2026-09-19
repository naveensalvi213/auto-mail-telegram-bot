# 1-Minute Koyeb Deployment Guide (24/7 Free Hosting)

Koyeb is a free 24/7 cloud platform designed for background workers and Telegram bots.

### Why Koyeb is Superior to Render for Email Outreach:
1. **Unrestricted Gmail SMTP**: Koyeb **allows outbound connections to ports 465 & 587**, so your 20 Gmail sender accounts + App Passwords send emails directly to all lead creators with zero firewall blocks.
2. **Never Sleeps**: Free Koyeb workers run **24/7 continuously** (0 sleeping).
3. **No Credit Card Required**.

---

### Step-by-Step 1-Minute Setup:

1. Open **[app.koyeb.com](https://app.koyeb.com)**.
2. Click **Sign in with GitHub** (using your account `naveensalvi213`).
3. Click **Create App** (top right) ➔ Select **GitHub**.
4. Select your repository: **`naveensalvi213/auto-mail-telegram-bot`**.
5. Set:
   - **Service Type**: Worker
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `python main.py`
6. Click **Deploy**.

🎉 **Done!** Koyeb will deploy your bot in 30 seconds, and your outreach campaign will send all emails directly via your Gmail accounts 24/7!
