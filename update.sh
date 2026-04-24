#!/usr/bin/env bash
set -e

echo "Pulling latest..."
git pull origin claude/discord-bot-mention-response-HWMc4

echo "Stopping bot..."
pkill -f bot.py 2>/dev/null || true

echo "Starting bot..."
source venv/bin/activate
exec python bot.py
