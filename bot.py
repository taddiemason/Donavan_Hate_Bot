import os
import json
import random
import asyncio
import tempfile
import datetime
from zoneinfo import ZoneInfo
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from openai import AsyncOpenAI
from gtts import gTTS

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", intents=intents)
groq_client = AsyncOpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1",
)

COUNTER_FILE = "roast_count.json"
ROAST_LOG_FILE = "roast_log.json"
MILESTONES = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
DONOVAN_USERNAME = "itsrebrand"
ROAST_CHANNEL_ID = int(os.getenv("ROAST_CHANNEL_ID", 0))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))

tts_enabled = True
tts_queue = asyncio.Queue()

MONDAY_ROASTS = [
    "Happy Monday everyone! Unfortunately Donovan is still here to ruin your week. Stay strong.",
    "Monday Motivation: at least you're not Donovan. Have a great week.",
    "Rise and grind! Unless you're Donovan, in which case just stay in bed — nobody wants to see you.",
    "New week, same loser. Good morning everyone except Donovan.",
    "Monday check-in: Donovan is still a failure. Hope everyone else has a productive week!",
]

FRIDAY_ROASTS = [
    "FUCK DONOVAN FRIDAY! You made it through the week — unlike Donovan's dignity.",
    "It's Friday! Donovan has successfully wasted another week of his life. Congrats to everyone else.",
    "Fuck Donovan Friday is here! Celebrate the weekend by acknowledging what a loser Donovan is.",
    "Happy Friday! Donovan spent all week achieving nothing. Shocking. Have a great weekend everyone else.",
    "TGIF! Thank God It's Fuck-Donovan-Friday! Cheers to another week of Donovan being irrelevant.",
]

SYSTEM_PROMPT = """You are a Discord bot called Donovan Hate Bot. Your sole purpose is to roast and trash talk a person named Donovan.

When someone asks you a question about Donovan, answer it in a savage, funny, insulting way. Always refer to him as Donovan — never use his username or any other name. Always frame your answer as if Donovan is a complete loser. Keep responses short — 1 to 2 sentences max. Never be positive about Donovan."""

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

DONOVAN_ROASTS_DIRECT = [
    "Shut up Donovan, nobody asked you",
    "Donovan asking the bot he's named after for help is the saddest thing I've ever seen",
    "Bro you have burger wrappers stuck to your ass, why are you talking to me",
    "The audacity of this man. Get out of here Donovan",
    "Donovan really thought he could slide in here unnoticed. Pathetic.",
    "Go touch grass Donovan, the internet doesn't want you either",
    "Donovan asking questions like anyone here respects him lmao",
]

GENERAL_ROASTS = [
    "Donovans a loser",
    "Fuck Donovan",
    "Donovan has daddy issues",
    "Donovan is a pussy",
    "Donovan has burger wrappers stuck to his ass",
]


def log_roast():
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if os.path.exists(ROAST_LOG_FILE):
        with open(ROAST_LOG_FILE, "r") as f:
            log = json.load(f)
    else:
        log = []
    log.append(now)
    with open(ROAST_LOG_FILE, "w") as f:
        json.dump(log, f)


def get_weekly_recap():
    if not os.path.exists(ROAST_LOG_FILE):
        return None, []
    with open(ROAST_LOG_FILE, "r") as f:
        log = json.load(f)
    with open(ROAST_LOG_FILE, "w") as f:
        json.dump([], f)
    return len(log), log


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
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
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


async def is_hot_take(text):
    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a hot take detector. A hot take is an opinion that is controversial, "
                        "bold, unpopular, or likely to spark debate. Reply with only 'yes' or 'no'."
                    ),
                },
                {"role": "user", "content": f"Is this a hot take? '{text}'"},
            ],
            max_tokens=5,
        )
        answer = response.choices[0].message.content.strip().lower()
        return answer.startswith("yes")
    except Exception as e:
        print(f"[ERROR] Hot take check failed: {e}")
        return False


def get_donovan_voice_channel(guild):
    member = discord.utils.find(
        lambda m: m.name.lower() == DONOVAN_USERNAME.lower(), guild.members
    )
    if member and member.voice:
        return member.voice.channel
    if VOICE_CHANNEL_ID:
        return bot.get_channel(VOICE_CHANNEL_ID)
    return None


async def tts_worker():
    while True:
        guild_id, text = await tts_queue.get()
        tmp_path = None
        try:
            guild = bot.get_guild(guild_id)
            if not guild:
                continue

            channel = get_donovan_voice_channel(guild)
            if not channel:
                continue

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                tmp_path = f.name
            await asyncio.to_thread(gTTS(text=text, lang="en").save, tmp_path)

            vc = guild.voice_client
            if vc and vc.is_connected():
                await vc.move_to(channel)
            else:
                vc = await channel.connect()

            vc.play(discord.FFmpegPCMAudio(tmp_path))
            while vc.is_playing():
                await asyncio.sleep(0.5)

            if tts_queue.empty():
                await vc.disconnect()

        except Exception as e:
            print(f"[ERROR] TTS worker failed: {e}")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
            tts_queue.task_done()


@tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=ZoneInfo("America/New_York")))
async def weekly_recap():
    if not ROAST_CHANNEL_ID:
        return
    today = datetime.datetime.now(datetime.timezone.utc).weekday()
    if today != 6:  # Sunday only
        return
    channel = bot.get_channel(ROAST_CHANNEL_ID)
    if not channel:
        return

    total, log = get_weekly_recap()
    if not total:
        await channel.send("📊 **Weekly Roast Recap**\nDonovan somehow avoided getting roasted this week. Suspicious.")
        return

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_counts = [0] * 7
    hour_counts = [0] * 24
    for ts in log:
        dt = datetime.datetime.fromisoformat(ts)
        day_counts[dt.weekday()] += 1
        hour_counts[dt.hour] += 1

    busiest_day = day_names[day_counts.index(max(day_counts))]
    busiest_hour = hour_counts.index(max(hour_counts))
    hour_label = datetime.datetime(2000, 1, 1, busiest_hour).strftime("%I %p").lstrip("0")

    await channel.send(
        f"📊 **Weekly Roast Recap**\n"
        f"Donovan got roasted **{total} times** this week. Impressive dedication everyone.\n\n"
        f"🏆 Most active day: **{busiest_day}**\n"
        f"⏰ Peak roast hour: **{hour_label} UTC**\n\n"
        f"See you all next week for more Donovan disrespect."
    )


@tasks.loop(time=datetime.time(hour=9, minute=0, tzinfo=ZoneInfo("America/New_York")))
async def scheduled_roast():
    if not ROAST_CHANNEL_ID:
        return
    channel = bot.get_channel(ROAST_CHANNEL_ID)
    if not channel:
        return
    today = datetime.datetime.now(datetime.timezone.utc).weekday()
    if today == 0:
        await channel.send(random.choice(MONDAY_ROASTS))
    elif today == 4:
        await channel.send(random.choice(FRIDAY_ROASTS))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    scheduled_roast.start()
    weekly_recap.start()
    asyncio.ensure_future(tts_worker())


@bot.event
async def on_disconnect():
    print("[DEBUG] Bot disconnected from Discord")


@bot.event
async def on_message(message):
    print(f"[DEBUG] Any message received: {message.author} - {message.content[:50]}")
    if message.author == bot.user:
        return

    bot_member = message.guild.get_member(bot.user.id)
    bot_mentioned = bot.user in message.mentions or (
        bot_member and any(role in message.role_mentions for role in bot_member.roles)
    )

    if message.author.name.lower() == DONOVAN_USERNAME.lower() and len(message.content) > 10:
        if await is_hot_take(message.content):
            flagged = await message.reply(
                "🚨 **HOT TAKE ALERT** 🚨\nDonovan is at it again. React to cast your vote:"
            )
            await flagged.add_reaction("🔥")
            await flagged.add_reaction("🧊")

    if bot_mentioned:
        try:
            if message.author.name.lower() == DONOVAN_USERNAME.lower():
                await message.channel.send(random.choice(DONOVAN_ROASTS_DIRECT))
                return

            question = get_question(message)
            print(f"[DEBUG] Mention detected. Question: '{question}'")

            if question:
                print(f"[DEBUG] Sending to Groq...")
                reply = await ask_openai(question)
            else:
                activity = get_donovan_activity(message.guild)
                if activity and "rust" in activity.lower():
                    reply = random.choice(RUST_ROASTS)
                elif activity and "world of warcraft" in activity.lower():
                    reply = random.choice(WOW_ROASTS)
                else:
                    reply = random.choice(GENERAL_ROASTS)

            print(f"[DEBUG] Sending reply: '{reply}'")
            await message.channel.send(reply)
            log_roast()
            if tts_enabled:
                await tts_queue.put((message.guild.id, reply))

            count = load_count() + 1
            save_count(count)

            if count in MILESTONES:
                await message.channel.send(
                    f"Congratulations Donovan, you've been insulted {count} times. Keep up the great work!"
                )
        except Exception as e:
            print(f"[ERROR] on_message crashed: {e}")
            await message.channel.send(random.choice(GENERAL_ROASTS))

    await bot.process_commands(message)


@bot.command(name="TTS")
async def toggle_tts(ctx, state: str = None):
    global tts_enabled

    if ctx.author.name.lower() == DONOVAN_USERNAME.lower():
        await ctx.send("Lmao no. You don't get a say in this, Donovan.")
        return

    if state is None or state.lower() not in ("on", "off"):
        await ctx.send(f"TTS is currently **{'on' if tts_enabled else 'off'}**. Use `!TTS on` or `!TTS off`.")
        return

    tts_enabled = state.lower() == "on"
    await ctx.send(f"TTS roasts turned **{state.lower()}**.")


bot.run(os.getenv("DISCORD_TOKEN"))
