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

## Admin Panel

When the bot starts it also launches a local web dashboard. Open it in your browser at:

```
http://localhost:47832
```

> If port 47832 is already in use the bot will automatically try 47833, 47834 … up to 47841. Check the terminal output for the actual port — it prints `Admin dashboard running at http://0.0.0.0:<port>` on startup.

### Logging in

The panel is password-protected. Set your password in `.env`:

```
ADMIN_PASSWORD=change_me_to_something_secret
```

If `ADMIN_PASSWORD` is not set it defaults to `admin` — **change this before exposing the port to a network**.

---

### Pages

#### Dashboard (`/`)
Overview of the economy at a glance:
- Total users and coins in circulation
- Today's shop rotation and time until it refreshes
- Top 5 coin balances
- Current stock prices

#### Economy (`/economy`)
Full leaderboard showing every user's cash, portfolio value, and net worth.

**Adjusting a user's coins:**
1. Enter the user's Discord ID in the **User ID** field (right-click a user in Discord → *Copy User ID*)
2. Enter an amount
3. Pick **Add**, **Remove**, or **Set** from the dropdown
4. Click **Apply**

You can also click any username in the table to go to their individual user page.

#### Shop (`/shop`)
Shows the items currently available in the daily shop rotation along with their cost and description, plus the time remaining until the rotation refreshes automatically.

**Force-resetting the shop:**  
Click **Reset Shop Now** to immediately cycle to a new set of items, excluding the current ones. Useful if you want to give the server a fresh selection without waiting for the daily timer.

#### Stocks (`/stocks`)
Lists every tracked stock with its current price and short-interest percentage (highlighted yellow above 10 %, red above 20 %).

**Overriding a stock price:**  
Each row has a price input. Change the value and click **Set** to pin the stock to that price. Normal drift will continue from the new value on the next tick.

#### User detail (`/user/<discord-id>`)
Drill into a specific user to see:
- Cash, portfolio value, and net worth summary cards
- Long stock positions (ticker, shares, current price, total value)
- Short positions with entry price, current price, and live P&L
- Inventory of shop items

You can also adjust that user's coin balance directly from this page.

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

### Option A — Discord command (easiest)

If the bot is already running, type this in any Discord channel you have admin access to:

```
!update
```

This will:
1. Pull the latest code from the current branch
2. Print the git output so you can see what changed
3. Kill all running bot instances with `pkill -f bot.py`
4. Your persistence setup (systemd, screen, etc.) will automatically restart it with the new code

> **Note:** If nothing changed, git will say `Already up to date.` and the bot will still restart cleanly.

---

### Option B — Manual (SSH into the server)

```bash
git pull origin claude/fix-sports-trivia-HBbRZ
pkill -f bot.py
source venv/bin/activate
python bot.py
```

Install any new dependencies first if `requirements.txt` changed:

```bash
pip install -r requirements.txt
```

---

### Option C — systemd restart

```bash
git pull origin claude/fix-sports-trivia-HBbRZ
sudo systemctl restart donavanbot
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
| `web_admin.py` | Admin dashboard web server |
| `requirements.txt` | Python dependencies |
| `.env.example` | Template for your bot token and admin password |
| `.gitignore` | Prevents `.env` from being committed |
