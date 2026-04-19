import os
import json
import random
import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

COUNTER_FILE = "roast_count.json"
MILESTONES = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
DONOVAN_USERNAME = "itsrebrand"

SYSTEM_PROMPT = """You are a Discord bot called Donovan Hate Bot. Your sole purpose is to roast and trash talk a person named Donovan (Discord: itsrebrand).

When someone asks you a question about Donovan, answer it in a savage, funny, insulting way. Always frame your answer as if Donovan is a complete loser. Keep responses short — 1 to 2 sentences max. Never be positive about Donovan."""

RUST_ROASTS = [
    "Donovan is playing Rust? More like getting naked and starving like the loser he is",
    "Donovan is out here playing Rust and still can't survive 10 minutes — shocking",
    "Donovan plays Rust because it's the closest he'll ever get to having friends",
    "Of course Donovan is playing Rust, he loves getting farmed by people better than him",
    "Donovan grinding Rust instead of grinding a personality",
]

WOW_ROASTS = [
    "Donovan is playing World of Warcraft — at least his virtual life is going somewhere",
    "Donovan is raiding WoW instead of touching grass. Embarrassing.",
    "Of course Donovan plays WoW, it's the only world where he isn't completely irrelevant",
    "Donovan has logged more hours in WoW than he has in the real world and it shows",
    "Donovan is out here playing WoW like it's 2007. Just like his haircut.",
]

GENERAL_ROASTS = [
    "Donovans a loser",
    "Fuck Donovan",
    "Donovan has daddy issues",
    "Donovan is a pussy",
    "Donovan has burger wrappers stuck to his ass",
]


def load_count():
    if os.path.exists(COUNTER_FILE):
        with open(COUNTER_FILE, "r") as f:
            return json.load(f).get("count", 0)
    return 0


def save_count(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)


def get_donovan_activity(guild):
    member = discord.utils.find(
        lambda m: m.name.lower() == DONOVAN_USERNAME.lower(), guild.members
    )
    if not member:
        print(f"[DEBUG] Could not find member: {DONOVAN_USERNAME}")
        return None
    print(f"[DEBUG] Found member: {member.name}, activities: {member.activities}")
    for activity in member.activities:
        print(f"[DEBUG] Activity: {activity} | Type: {type(activity)}")
        if isinstance(activity, (discord.Game, discord.Activity)):
            return activity.name
    return None


def get_question(message):
    text = message.content
    for mention in message.mentions:
        text = text.replace(f"<@{mention.id}>", "").replace(f"<@!{mention.id}>", "")
    return text.strip()


async def ask_openai(question):
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[ERROR] OpenAI request failed: {e}")
        return random.choice(GENERAL_ROASTS)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        question = get_question(message)

        if question:
            reply = await ask_openai(question)
        else:
            activity = get_donovan_activity(message.guild)
            if activity and "rust" in activity.lower():
                reply = random.choice(RUST_ROASTS)
            elif activity and "world of warcraft" in activity.lower():
                reply = random.choice(WOW_ROASTS)
            else:
                reply = random.choice(GENERAL_ROASTS)

        await message.channel.send(reply)

        count = load_count() + 1
        save_count(count)

        if count in MILESTONES:
            await message.channel.send(
                f"Congratulations Donovan, you've been insulted {count} times. Keep up the great work!"
            )

    await bot.process_commands(message)


bot.run(os.getenv("DISCORD_TOKEN"))
