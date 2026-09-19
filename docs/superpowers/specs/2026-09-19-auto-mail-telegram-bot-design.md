# Design Specification: Auto Mail Telegram Bot

**Date**: 2026-09-19  
**Target Group ID**: `-5536170059`  
**Bot Token**: `8460543006:AAGKnlnbTPSkg7vGntQISVuL5vomjiNeiBk`

---

## 1. Executive Summary & Goals
The **Auto Mail Telegram Bot** is a Telegram-integrated automated email outreach engine designed for high deliverability, human-like sending patterns, and lead list processing directly within a Telegram group. Users can upload lead documents (`.xlsx`, `.csv`, `.json`), select from configured mail sender sets and template sets, and launch campaigns with randomized delays (20–60s) and sender rotation.

---

## 2. System Architecture

```
                                +-------------------+
                                |  Telegram Group   |
                                | (ID: -5536170059) |
                                +---------+---------+
                                          |
                                          v
                              +-----------------------+
                              | Telegram Bot (aiogram/|
                              | python-telegram-bot)  |
                              +-----------+-----------+
                                          |
         +--------------------------------+--------------------------------+
         |                                |                                |
         v                                v                                v
+------------------+            +------------------+            +------------------+
| Lead File Parser |            | SQLite Database  |            | Email Dispatcher |
| (.xlsx/.csv/.json|            | (Leads, Sets,    |            | (SMTP Rotation,  |
| extraction)      |            | Templates, Logs) |            | 20s-60s Delay)   |
+------------------+            +------------------+            +--------+---------+
                                                                         |
                                                                         v
                                                                +------------------+
                                                                |   Gmail SMTP     |
                                                                | (App Passwords)  |
                                                                +------------------+
```

### Components
1. **Telegram Handler (`bot/handlers.py`)**: Manages commands, file uploads (`.csv`, `.xlsx`, `.json`), inline button interactions, and user guidance.
2. **Database Engine (`database/db.py`)**: SQLite interface managing sender accounts, template sets, lead lists, campaign state, and logs.
3. **Lead Extractor (`utils/parser.py`)**: Parses uploaded spreadsheets/JSON files, extracts `Channel Name` and `Primary Email`, cleans invalid emails, and returns structured records.
4. **Outreach Engine (`engine/mailer.py`)**:
   - Manages asynchronous campaign background tasks.
   - Rotates sender Gmail accounts in the active Mail Set.
   - Generates personalized subject lines and email bodies by replacing `[Channel Name]` placeholders.
   - Applies random delay (20 to 60 seconds) between sends.
   - Updates campaign progress in the Telegram Group.

---

## 3. Pre-Configured Data Specifications

### Mail Sets (Gmail SMTP with App Passwords)

#### Mail Set 1 (10 Sender Accounts)
1. `salvinaveen478@gmail.com` | `hwbajpgwoexmxdjl`
2. `salvinaveen11@gmail.com` | `ofbmrbewgapjdjib`
3. `salvinaveen53@gmail.com` | `pxpdhlvyofkfjvtb`
4. `naveensalvi122@gmail.com` | `pfifzeejscjhxpyz`
5. `narusalvi142@gmail.com` | `diwnuipjmvrbplav`
6. `neoscale005@gmail.com` | `tlfqvififghvhwwd`
7. `editsneo63@gmail.com` | `wrracphhzummbquc`
8. `neoscale459@gmail.com` | `mssvxzanbyhqiuqg`
9. `nuclearstudiohq@gmail.com` | `cxuoofxqpebkjlcx`
10. `nuclearedithq@gmail.com` | `xehwlbobdnmuwppw`

#### Mail Set 2 (10 Sender Accounts)
1. `neocollabe@gmail.com` | `alwtgliymjsdzozc`
2. `neostudion@gmail.com` | `cjptbckgnnbhhzlp`
3. `neoscale004@gmail.com` | `puoesuzjnyusfgte`
4. `neoscale001@gmail.com` | `lbdcbwihdjkzwvpj`
5. `naveen.salvi02@gmail.com` | `vrwxbwvzawkpevhw`
6. `naveensalvi0202@gmail.com` | `efpqhcjtfcbzsthr`
7. `alexwilliams0621@gmail.com` | `diuqjekvxbecnxkz`
8. `tylerbrooks0621@gmail.com` | `mutgzodvsqiyfdvc`
9. `editsalex99@gmail.com` | `qvsgetegxzaehgjb`
10. `xeno.smma@gmail.com` | `kmwoximojpnfdfao`

---

### Template Sets

#### Template Set 1 (User Provided Templates)
1. **Subject**: `We’d like to build this for [Channel Name], free`
   **Body**:
   ```text
   Hey [Channel Name],

   We came across your channel and noticed a few things that could potentially be improved with AI automation.

   We’re currently building our portfolio, so we’d love to build an automation system for your channel completely free.

   There’s no payment or commitment. If you’re happy with the result, we’d simply ask for an honest review that we can feature in our portfolio.

   Would you be open to it?
   ```
*(... Templates 2 through 10 as specified in prompt)*

#### Template Set 2 (High-Converting Variation Set)
10 crafted cold outreach templates tailored for AI workflow & automation, featuring `[Channel Name]` subject and body placeholders.

---

## 4. Bot Commands & Workflow

1. **Lead File Upload**:
   - User drops `.csv`, `.xlsx`, or `.json` in group chat `-5536170059`.
   - Bot parses file and responds with a summary:
     > 📊 **Lead File Received!**  
     > Total extracted leads: **45**  
     > Valid emails: **45**  
     >  
     > Please select the **Mail Set** and **Template Set** to start.
2. **Interactive Inline Selection**:
   - Buttons: `[ Mail Set 1 ]` `[ Mail Set 2 ]`
   - Buttons: `[ Template Set 1 ]` `[ Template Set 2 ]`
   - Button: `[ 🚀 Start Campaign ]`
3. **Dynamic Commands**:
   - `/id` or `/groupid`: Outputs current Chat/Group ID.
   - `/addemail <set_id_or_name> <email> <app_password>`: Adds a new sender email to a mail set.
   - `/addtemplate <set_id_or_name>`: Starts prompt to add a new template subject & body.
   - `/listemails`: Lists all mail sets and active sender accounts.
   - `/listtemplates`: Lists all template sets and template contents.
   - `/status`: Shows active campaign status, progress, current sender, and delay countdown.
   - `/pause`: Pauses running campaign.
   - `/resume`: Resumes paused campaign.
   - `/cancel`: Cancels current campaign.

---

## 5. Deliverability & Human-like Sending Protocol
- **Random Delay**: `random.randint(20, 60)` seconds between consecutive messages.
- **Account Rotation**: Selects a random sender account from the active Mail Set for each email, preventing velocity flags on any single Gmail address.
- **Connection Management**: Opens SMTP SSL connection per message (or per batch with strict timeout), sends email, and cleanly disconnects.
- **Randomized Template Selection**: Cycles through available templates in the selected template set to avoid identical content detection.

---

## 6. Testing & Verification Strategy
- **Unit Tests**: Test parser logic for `.csv`, `.xlsx`, and `.json`.
- **Database Tests**: Test set creation, template addition, and email account management.
- **SMTP Verification**: Test connection and authentication for provided Gmail credentials.
- **Integration Test**: Mock or send test email using configured bot to verify Telegram notifications and queue management.
