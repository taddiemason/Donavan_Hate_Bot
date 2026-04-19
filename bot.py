import os
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


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

    await bot.process_commands(message)


bot.run(os.getenv("DISCORD_TOKEN"))
