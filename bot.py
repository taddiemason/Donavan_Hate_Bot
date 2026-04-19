import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

COUNTER_FILE = "roast_count.json"
MILESTONES = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]


def load_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f).get("count", 0)
    return 0


def save_count(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        responses = [
            "Donovans a loser",
            "Fuck Donovan",
            "Donovan has daddy issues",
            "Donovan is a pussy",
            "Donovan has burger wrappers stuck to his ass",
        ]
        await message.channel.send(random.choice(responses))

        count = load_count() + 1
        save_count(count)

        if count in MILESTONES:
            await message.channel.send(
                f"Congratulations Donovan, you've been insulted {count} times. Keep up the great work!"
            )

    await bot.process_commands(message)


bot.run(os.getenv("DISCORD_TOKEN"))
