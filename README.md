# Donavan Hate Bot

A Discord bot that roasts Donovan every time it gets @mentioned.

---

## Prerequisites

- Python 3.8 or higher
- A Discord account
- A server where you have admin permissions

---

## Step 1 — Create the Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name (e.g. `DonavanHateBot`)
3. In the left sidebar, click **Bot**
4. Click **Add Bot** → **Yes, do it!**
5. Under the bot's username, click **Reset Token** and copy the token — you'll need this later
6. Scroll down to **Privileged Gateway Intents** and enable:
   - **Message Content Intent**
7. Click **Save Changes**

---

## Step 2 — Invite the Bot to Your Server

1. In the left sidebar, click **OAuth2** → **URL Generator**
2. Under **Scopes**, check `bot`
3. Under **Bot Permissions**, check:
   - `Send Messages`
   - `Read Message History`
   - `View Channels`
4. Copy the generated URL at the bottom and open it in your browser
5. Select your server and click **Authorize**

---

## Step 3 — Set Up the Project

Clone the repository and enter the project folder:

```bash
git clone https://github.com/taddiemason/Donavan_Hate_Bot.git
cd Donavan_Hate_Bot
```

Create and activate a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## Step 4 — Configure Your Token

Copy the example env file:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and replace the placeholder with your bot token from Step 1:

```
DISCORD_TOKEN=your_actual_token_here
```

---

## Step 5 — Run the Bot

```bash
python bot.py
```

You should see output like:

```
Logged in as DonavanHateBot#1234 (ID: 123456789)
```

The bot is now live. @mention it in any channel and it will respond with a random Donovan roast.

---

## Keeping the Bot Running 24/7

By default the bot stops when you close your terminal. To keep it running persistently:

### Option A — systemd (Linux)

Create a service file at `/etc/systemd/system/donavanbot.service`:

```ini
[Unit]
Description=Donavan Hate Bot
After=network.target

[Service]
User=YOUR_LINUX_USER
WorkingDirectory=/path/to/Donavan_Hate_Bot
EnvironmentFile=/path/to/Donavan_Hate_Bot/.env
ExecStart=/path/to/Donavan_Hate_Bot/venv/bin/python bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable donavanbot
sudo systemctl start donavanbot
```

### Option B — screen (Linux/macOS, quick & simple)

```bash
screen -S donavanbot
python bot.py
# Press Ctrl+A then D to detach — bot keeps running in background
```

### Option C — Hosting on a VPS

Deploy the project to any VPS (DigitalOcean, Linode, AWS EC2, etc.), follow the Linux setup above, and the bot will run 24/7 without needing your computer on.

---

## Updating the Bot

Since the bot is already running (e.g. via systemd or screen), the update process is:

1. **Pull the latest code:**
   ```bash
   git pull origin main
   ```

2. **Install any new dependencies** (only needed if `requirements.txt` changed):
   ```bash
   pip install -r requirements.txt
   ```

3. **Restart the bot** so it picks up the changes:

   - **systemd:**
     ```bash
     sudo systemctl restart donavanbot
     ```
   - **screen:** Kill the old session and start a new one:
     ```bash
     screen -r donavanbot
     # Press Ctrl+C to stop the bot
     python bot.py
     # Press Ctrl+A then D to detach
     ```

---

## Troubleshooting

### Bot sending duplicate replies

If the bot sends two roasts per mention, it means two instances are running at the same time. This happens if you started the bot manually AND via systemd, or started it twice in a screen session.

Check for multiple running instances:

```bash
ps aux | grep bot.py
```

Kill them all:

```bash
pkill -f bot.py
```

Then start just one instance — either manually:

```bash
source venv/bin/activate
python bot.py
```

Or via systemd:

```bash
sudo systemctl start donavanbot
```

Don't run both manually and via systemd at the same time — pick one method and stick to it.

---

## File Overview

| File | Purpose |
|------|---------|
| `bot.py` | Main bot logic |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for your bot token |
| `.gitignore` | Prevents `.env` from being committed |
