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
ECONOMY_FILE = "economy.json"
MILESTONES = [10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000]
DONOVAN_USERNAME = "itsrebrand"
ROAST_CHANNEL_ID = int(os.getenv("ROAST_CHANNEL_ID", 0))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))
INSURANCE_COST_PER_MINUTE = 10
MAX_INSURANCE_MINUTES = 30

SHOP_ITEMS = {
    "double_roast": {
        "name": "Double Roast",
        "cost": 100,
        "description": "Your next @mention fires TWO roasts back to back",
    },
    "mega_roast": {
        "name": "Mega Roast",
        "cost": 200,
        "description": "Your next @mention also triggers an AI-generated extra savage bonus roast",
    },
    "shame_bell": {
        "name": "Shame Bell",
        "cost": 50,
        "description": "Next roast comes with a 🔔 SHAME 🔔 announcement",
    },
    "snitch": {
        "name": "Snitch",
        "cost": 75,
        "description": "Next roast also gets DMed directly to Donovan",
    },
    "triple_roast": {
        "name": "Triple Roast",
        "cost": 125,
        "description": "Next roast fires THREE times in a row",
    },
    "anonymous": {
        "name": "Anonymous",
        "cost": 150,
        "description": "Next roast is delivered as an anonymous tip",
    },
    "spotlight": {
        "name": "Spotlight",
        "cost": 175,
        "description": "Next roast pings @here so nobody misses it",
    },
    "hall_of_shame": {
        "name": "Hall of Shame",
        "cost": 250,
        "description": "Next roast gets pinned in the channel permanently",
    },
    "scorched_earth": {
        "name": "Scorched Earth",
        "cost": 300,
        "description": "AI generates 3 different unique roasts back to back",
    },
    "bounty_boost": {
        "name": "Bounty Boost",
        "cost": 350,
        "description": "Your next bounty claim pays out double",
    },
    "exile": {
        "name": "Exile",
        "cost": 400,
        "description": "Timeouts Donovan in the server for 60 seconds (requires bot Moderate Members permission)",
    },
    "nuclear": {
        "name": "Nuclear",
        "cost": 500,
        "description": "Maximum AI roast + forces TTS even if it's off",
    },
}

tts_enabled = True
tts_queue = asyncio.Queue()
trial_active = False
guess_game_active = False

QUOTES = [
    {"text": "Big Macs are honestly underrated and I will die on this hill.", "is_donovan": True},
    {"text": "I would win at Rust if people just stopped killing me.", "is_donovan": True},
    {"text": "I'm not saying I'm the smartest person in the room, I'm just saying everyone else is dumb.", "is_donovan": True},
    {"text": "She was a big girl but she had a great personality.", "is_donovan": True},
    {"text": "Bro I was top fragging until my internet cut out.", "is_donovan": True},
    {"text": "I don't have daddy issues I just don't like authority.", "is_donovan": True},
    {"text": "The McDouble is actually a better value than the Big Mac and I'll prove it.", "is_donovan": True},
    {"text": "I could go pro if I actually tried.", "is_donovan": True},
    {"text": "Be the change you wish to see in the world.", "is_donovan": False},
    {"text": "The only way to do great work is to love what you do.", "is_donovan": False},
    {"text": "In the middle of every difficulty lies opportunity.", "is_donovan": False},
    {"text": "It does not matter how slowly you go as long as you do not stop.", "is_donovan": False},
    {"text": "Life is what happens when you're busy making other plans.", "is_donovan": False},
    {"text": "The unexamined life is not worth living.", "is_donovan": False},
    {"text": "To be yourself in a world that is constantly trying to make you something else is the greatest accomplishment.", "is_donovan": False},
    {"text": "Two things are infinite: the universe and human stupidity.", "is_donovan": False},
]

SENTENCES = [
    "Donovan is sentenced to a lifetime of being himself — the cruelest punishment this court can impose.",
    "Donovan is hereby sentenced to 10 years of mandatory grass-touching, effective immediately.",
    "The court sentences Donovan to a permanent ban from Big Mac meals and all associated large women.",
    "Donovan is sentenced to listen to his own opinions on repeat for eternity. God help him.",
    "By the power vested in this bot, Donovan is sentenced to public humiliation every day until further notice. Court adjourned.",
    "Donovan is sentenced to 500 hours of community service, specifically apologizing to everyone who has ever had to interact with him.",
    "The court finds no punishment severe enough, so Donovan is sentenced to simply continue being Donovan. Brutal.",
]

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


def load_economy():
    if os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "r") as f:
            return json.load(f)
    return {"balances": {}, "bounties": [], "insurance_expires": None,
            "pending_upgrades": {}, "market_listings": [],
            "next_bounty_id": 1, "next_listing_id": 1}


def save_economy(data):
    with open(ECONOMY_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_coins(user_id, amount):
    eco = load_economy()
    uid = str(user_id)
    eco["balances"][uid] = eco["balances"].get(uid, 0) + amount
    save_economy(eco)


def spend_coins(user_id, amount):
    eco = load_economy()
    uid = str(user_id)
    bal = eco["balances"].get(uid, 0)
    if bal < amount:
        return False
    eco["balances"][uid] = bal - amount
    save_economy(eco)
    return True


def is_insurance_active():
    exp = load_economy().get("insurance_expires")
    if not exp:
        return False
    return datetime.datetime.fromisoformat(exp) > datetime.datetime.now(datetime.timezone.utc)


def consume_upgrade(user_id, upgrade):
    eco = load_economy()
    uid = str(user_id)
    upgrades = eco.get("pending_upgrades", {}).get(uid, [])
    if upgrade in upgrades:
        upgrades.remove(upgrade)
        eco["pending_upgrades"][uid] = upgrades
        save_economy(eco)
        return True
    return False


def has_upgrade(user_id, upgrade):
    eco = load_economy()
    return upgrade in eco.get("pending_upgrades", {}).get(str(user_id), [])


def claim_bounties(user_id):
    eco = load_economy()
    active = [b for b in eco["bounties"] if b["active"]]
    total = sum(b["amount"] for b in active)
    if total > 0:
        uid = str(user_id)
        upgrades = eco.get("pending_upgrades", {}).get(uid, [])
        if "bounty_boost" in upgrades:
            upgrades.remove("bounty_boost")
            eco["pending_upgrades"][uid] = upgrades
            total *= 2
    for b in eco["bounties"]:
        b["active"] = False
    save_economy(eco)
    return total


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

    if message.author.name.lower() == DONOVAN_USERNAME.lower():
        add_coins(message.author.id, 1)

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

            if is_insurance_active():
                await message.channel.send("🛡️ Donovan's insurance is active... unfortunately it doesn't cover being a loser.")

            # Build the final roast message applying upgrades
            send_text = reply
            force_tts = False

            if consume_upgrade(message.author.id, "shame_bell"):
                await message.channel.send("🔔 **SHAME** 🔔 🔔 **SHAME** 🔔 🔔 **SHAME** 🔔")

            if consume_upgrade(message.author.id, "anonymous"):
                send_text = f"📨 *An anonymous source says:* {reply}"

            if consume_upgrade(message.author.id, "spotlight"):
                send_text = f"@here {send_text}"

            if consume_upgrade(message.author.id, "nuclear"):
                nuclear_text = await ask_openai("Give the single most devastating, savage, all-out roast of Donovan humanly possible. No mercy.")
                send_text = f"☢️ **NUCLEAR ROAST:** {nuclear_text}"
                force_tts = True

            sent_msg = await message.channel.send(send_text)
            log_roast()

            if tts_enabled or force_tts:
                await tts_queue.put((message.guild.id, send_text))

            if consume_upgrade(message.author.id, "snitch"):
                donovan = discord.utils.find(lambda m: m.name.lower() == DONOVAN_USERNAME.lower(), message.guild.members)
                if donovan:
                    try:
                        await donovan.send(f"📬 Someone wanted you to see this:\n_{reply}_")
                    except Exception:
                        pass

            if consume_upgrade(message.author.id, "hall_of_shame"):
                try:
                    await sent_msg.pin()
                except Exception:
                    pass

            if consume_upgrade(message.author.id, "double_roast"):
                await message.channel.send(f"⚡ **DOUBLE ROAST:** {reply}")

            if consume_upgrade(message.author.id, "triple_roast"):
                await message.channel.send(reply)
                await message.channel.send(f"⚡ **TRIPLE ROAST:** {reply}")

            if consume_upgrade(message.author.id, "mega_roast"):
                mega = await ask_openai("Give the most savage, creative, brutal roast about Donovan you can. Go all out.")
                await message.channel.send(f"💥 **MEGA ROAST:** {mega}")

            if consume_upgrade(message.author.id, "scorched_earth"):
                for i in range(3):
                    roast = await ask_openai(f"Give a unique savage roast about Donovan. Make it different each time. Roast #{i+1}.")
                    await message.channel.send(f"🔥 {roast}")

            if consume_upgrade(message.author.id, "exile"):
                donovan = discord.utils.find(lambda m: m.name.lower() == DONOVAN_USERNAME.lower(), message.guild.members)
                if donovan:
                    try:
                        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60)
                        await donovan.timeout(until, reason="Exile purchased by the people.")
                        await message.channel.send("⛔ Donovan has been exiled for 60 seconds. Enjoy the peace.")
                    except Exception:
                        await message.channel.send("⛔ Exile failed — bot needs Moderate Members permission.")

            add_coins(message.author.id, 10)
            bounty_total = claim_bounties(message.author.id)
            if bounty_total > 0:
                add_coins(message.author.id, bounty_total)
                await message.channel.send(f"💰 {message.author.mention} collected **{bounty_total} Roast Coins** in active bounties!")

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


@bot.command(name="Commands")
async def commands_list(ctx):
    await ctx.send(
        "**📋 Donovan Hate Bot — Commands**\n\n"
        "**`@Donovan Hate Bot`** — Roasts Donovan. Ask it a question for a smart response.\n"
        "**`!Trial <reason>`** — Puts Donovan on trial. Server votes guilty/not guilty for 60 seconds.\n"
        "**`!Guesswhosaidit`** — 3 round game. Guess if the quote was Donovan or someone else.\n"
        "**`!TTS on/off`** — Toggles voice channel roasts. (Donovan cannot use this.)\n\n"
        "**💰 Economy**\n"
        "**`!balance`** — Check your Roast Coin balance.\n"
        "**`!leaderboard`** — Top 5 coin holders.\n"
        "**`!shop`** — View upgrades for sale.\n"
        "**`!buy <item>`** — Purchase an upgrade.\n"
        "**`!bounty <amount> <description>`** — Post a bounty paid to whoever triggers the next roast.\n"
        "**`!bounties`** — View active bounties.\n"
        "**`!insurance <minutes>`** — Donovan only: buy temporary (useless) protection.\n"
        "**`!give @user <amount>`** — Transfer coins to another member.\n"
        "**`!blackmarket`** — View peer-to-peer upgrade listings.\n"
        "**`!listitem <item> <price>`** — List an owned upgrade for sale.\n"
        "**`!buyitem <id>`** — Buy an upgrade from the black market.\n\n"
        "**`!Commands`** — Shows this list.\n"
    )


@bot.command(name="balance")
async def balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    bal = load_economy()["balances"].get(str(target.id), 0)
    await ctx.send(f"💰 **{target.display_name}** has **{bal} Roast Coins**.")


@bot.command(name="leaderboard")
async def leaderboard(ctx):
    eco = load_economy()
    top = sorted(eco["balances"].items(), key=lambda x: x[1], reverse=True)[:5]
    if not top:
        await ctx.send("Nobody has earned any Roast Coins yet.")
        return
    lines = []
    for i, (uid, coins) in enumerate(top, 1):
        member = ctx.guild.get_member(int(uid))
        name = member.display_name if member else "Unknown"
        lines.append(f"{i}. **{name}** — {coins} coins")
    await ctx.send("💰 **Roast Coin Leaderboard**\n" + "\n".join(lines))


@bot.command(name="shop")
async def shop(ctx):
    lines = [f"**{v['name']}** (`{k}`) — {v['cost']} coins\n_{v['description']}_"
             for k, v in SHOP_ITEMS.items()]
    await ctx.send("🛒 **Roast Shop**\n\n" + "\n\n".join(lines) + "\n\nUse `!buy <item>` to purchase.")


@bot.command(name="buy")
async def buy_item(ctx, item_name: str = None):
    if not item_name or item_name.lower() not in SHOP_ITEMS:
        await ctx.send(f"Unknown item. Use `!shop` to see available items.")
        return
    item = SHOP_ITEMS[item_name.lower()]
    if not spend_coins(ctx.author.id, item["cost"]):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**, this costs **{item['cost']}**.")
        return
    eco = load_economy()
    eco.setdefault("pending_upgrades", {}).setdefault(str(ctx.author.id), []).append(item_name.lower())
    save_economy(eco)
    await ctx.send(f"✅ Purchased **{item['name']}**! It activates on your next @mention of the bot.")


@bot.command(name="bounty")
async def post_bounty(ctx, amount: int = None, *, description: str = None):
    if ctx.author.name.lower() == DONOVAN_USERNAME.lower():
        await ctx.send("Donovan cannot post bounties. He IS the bounty.")
        return
    if not amount or not description or amount <= 0:
        await ctx.send("Usage: `!bounty <amount> <description>`")
        return
    if not spend_coins(ctx.author.id, amount):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**.")
        return
    eco = load_economy()
    bid = eco.get("next_bounty_id", 1)
    eco["bounties"].append({"id": bid, "poster_id": str(ctx.author.id),
                            "amount": amount, "description": description, "active": True})
    eco["next_bounty_id"] = bid + 1
    save_economy(eco)
    await ctx.send(f"🎯 **Bounty #{bid} posted!**\n_{description}_\n💰 Reward: **{amount} coins** to whoever triggers the next roast!")


@bot.command(name="bounties")
async def view_bounties(ctx):
    active = [b for b in load_economy()["bounties"] if b["active"]]
    if not active:
        await ctx.send("🎯 No active bounties. Post one with `!bounty <amount> <description>`.")
        return
    lines = [f"**#{b['id']}** — {b['amount']} coins\n_{b['description']}_" for b in active]
    await ctx.send("🎯 **Active Bounties**\n\n" + "\n\n".join(lines))


@bot.command(name="insurance")
async def insurance(ctx, minutes: int = None):
    if ctx.author.name.lower() != DONOVAN_USERNAME.lower():
        await ctx.send("Only Donovan needs insurance. Everyone else is fine.")
        return
    if not minutes or minutes <= 0:
        await ctx.send(f"Usage: `!insurance <minutes>` — costs {INSURANCE_COST_PER_MINUTE} coins/min (max {MAX_INSURANCE_MINUTES} min).")
        return
    minutes = min(minutes, MAX_INSURANCE_MINUTES)
    cost = minutes * INSURANCE_COST_PER_MINUTE
    if not spend_coins(ctx.author.id, cost):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins Donovan. You have **{bal}**, you need **{cost}**. Keep chatting to earn more.")
        return
    expires = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=minutes)
    eco = load_economy()
    eco["insurance_expires"] = expires.isoformat()
    save_economy(eco)
    await ctx.send(f"🛡️ Donovan bought **{minutes} minutes** of insurance for **{cost} coins**. Cute. Won't save him though.")


@bot.command(name="give")
async def give_coins(ctx, member: discord.Member = None, amount: int = None):
    if not member or not amount or amount <= 0:
        await ctx.send("Usage: `!give @user <amount>`")
        return
    if member.id == ctx.author.id:
        await ctx.send("You can't give coins to yourself.")
        return
    if not spend_coins(ctx.author.id, amount):
        await ctx.send("Not enough coins.")
        return
    add_coins(member.id, amount)
    await ctx.send(f"💸 **{ctx.author.display_name}** sent **{amount} Roast Coins** to **{member.display_name}**.")


@bot.command(name="blackmarket")
async def black_market(ctx):
    listings = [l for l in load_economy().get("market_listings", []) if l["active"]]
    if not listings:
        await ctx.send("🕶️ **Black Market**\nNo listings right now. Use `!listitem <item> <price>` to sell an upgrade.")
        return
    lines = []
    for l in listings:
        seller = ctx.guild.get_member(int(l["seller_id"]))
        name = seller.display_name if seller else "Unknown"
        item = SHOP_ITEMS.get(l["item"], {}).get("name", l["item"])
        lines.append(f"**#{l['id']}** — {item} by {name} — {l['price']} coins  →  `!buyitem {l['id']}`")
    await ctx.send("🕶️ **Black Market**\n\n" + "\n".join(lines))


@bot.command(name="listitem")
async def list_item(ctx, item_name: str = None, price: int = None):
    if not item_name or not price or price <= 0:
        await ctx.send("Usage: `!listitem <item_name> <price>`")
        return
    item_name = item_name.lower()
    if item_name not in SHOP_ITEMS:
        await ctx.send(f"Unknown item. Valid items: {', '.join(SHOP_ITEMS.keys())}")
        return
    if not consume_upgrade(ctx.author.id, item_name):
        await ctx.send(f"You don't own a **{SHOP_ITEMS[item_name]['name']}** to sell.")
        return
    eco = load_economy()
    lid = eco.get("next_listing_id", 1)
    eco.setdefault("market_listings", []).append(
        {"id": lid, "seller_id": str(ctx.author.id), "item": item_name, "price": price, "active": True}
    )
    eco["next_listing_id"] = lid + 1
    save_economy(eco)
    await ctx.send(f"🕶️ Listed **{SHOP_ITEMS[item_name]['name']}** for **{price} coins** on the black market (ID #{lid}).")


@bot.command(name="buyitem")
async def buy_market_item(ctx, listing_id: int = None):
    if not listing_id:
        await ctx.send("Usage: `!buyitem <listing_id>`")
        return
    eco = load_economy()
    listing = next((l for l in eco.get("market_listings", []) if l["id"] == listing_id and l["active"]), None)
    if not listing:
        await ctx.send("Listing not found or already sold.")
        return
    if listing["seller_id"] == str(ctx.author.id):
        await ctx.send("You can't buy your own listing.")
        return
    if not spend_coins(ctx.author.id, listing["price"]):
        await ctx.send("Not enough coins.")
        return
    add_coins(int(listing["seller_id"]), listing["price"])
    listing["active"] = False
    eco.setdefault("pending_upgrades", {}).setdefault(str(ctx.author.id), []).append(listing["item"])
    save_economy(eco)
    seller = ctx.guild.get_member(int(listing["seller_id"]))
    seller_name = seller.display_name if seller else "Unknown"
    item_name = SHOP_ITEMS.get(listing["item"], {}).get("name", listing["item"])
    await ctx.send(f"🕶️ **{ctx.author.display_name}** bought **{item_name}** from **{seller_name}** for **{listing['price']} coins**.")


@bot.command(name="Guesswhosaidit")
async def guess_who(ctx):
    global guess_game_active

    if ctx.author.name.lower() == DONOVAN_USERNAME.lower():
        await ctx.send("You're not allowed to play this game Donovan. You might recognise yourself.")
        return

    if guess_game_active:
        await ctx.send("A game is already running. One humiliation at a time.")
        return

    guess_game_active = True
    scores = {}
    pool = random.sample(QUOTES, min(3, len(QUOTES)))

    try:
        await ctx.send("🎮 **GUESS WHO SAID IT** 🎮\n3 rounds, 30 seconds each.\nReact 🇩 if you think **Donovan** said it, 🤷 if **someone else** did.")

        for round_num, quote in enumerate(pool, 1):
            msg = await ctx.send(
                f"**Round {round_num}/3**\n\n"
                f'*"{quote["text"]}"*\n\n'
                f"🇩 = Donovan    🤷 = Not Donovan"
            )
            await msg.add_reaction("🇩")
            await msg.add_reaction("🤷")

            await asyncio.sleep(30)

            msg = await ctx.channel.fetch_message(msg.id)
            donovan_voters = set()
            not_donovan_voters = set()

            for reaction in msg.reactions:
                async for user in reaction.users():
                    if user.bot:
                        continue
                    if str(reaction.emoji) == "🇩":
                        donovan_voters.add(user.id)
                    elif str(reaction.emoji) == "🤷":
                        not_donovan_voters.add(user.id)

            correct_voters = donovan_voters if quote["is_donovan"] else not_donovan_voters
            for uid in correct_voters:
                scores[uid] = scores.get(uid, 0) + 1

            answer = "**DONOVAN** said that. Shocking." if quote["is_donovan"] else "A normal human said that. Donovan could never."
            correct_count = len(correct_voters)
            await ctx.send(f"⏱️ Time's up! {answer}\n✅ {correct_count} people got it right.")

        if scores:
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            winner_id, top_score = sorted_scores[0]
            winner = ctx.guild.get_member(winner_id)
            winner_name = winner.display_name if winner else "Someone"
            board = "\n".join(
                f"{ctx.guild.get_member(uid).display_name if ctx.guild.get_member(uid) else 'Unknown'}: {s}/3"
                for uid, s in sorted_scores
            )
            await ctx.send(
                f"🏆 **GAME OVER**\n\n{board}\n\n"
                f"Winner: **{winner_name}** with {top_score}/3 — the only one here who truly understands how big of a loser Donovan is."
            )
        else:
            await ctx.send("🏆 **GAME OVER**\nNobody scored a single point. Donovan would fit right in.")

    except Exception as e:
        print(f"[ERROR] Guess game failed: {e}")
        await ctx.send("The game crashed. Blame Donovan.")
    finally:
        guess_game_active = False


@bot.command(name="Trial")
async def trial(ctx, *, reason: str = None):
    global trial_active

    if ctx.author.name.lower() == DONOVAN_USERNAME.lower():
        await ctx.send("You can't put yourself on trial Donovan. Though honestly you should.")
        return

    if trial_active:
        await ctx.send("A trial is already in progress. Donovan can only be humiliated one case at a time.")
        return

    if not reason:
        await ctx.send("You need to provide a charge. Usage: `!Trial <reason>`")
        return

    trial_active = True
    try:
        msg = await ctx.send(
            f"⚖️ **THE PEOPLE VS. DONOVAN** ⚖️\n\n"
            f"**Charge:** {reason}\n\n"
            f"Cast your vote:\n"
            f"👨‍⚖️ = GUILTY\n"
            f"🆓 = NOT GUILTY\n\n"
            f"_Voting closes in 60 seconds._"
        )
        await msg.add_reaction("👨‍⚖️")
        await msg.add_reaction("🆓")

        await asyncio.sleep(60)

        msg = await ctx.channel.fetch_message(msg.id)
        guilty = 0
        not_guilty = 0
        for reaction in msg.reactions:
            if str(reaction.emoji) == "👨‍⚖️":
                guilty = reaction.count - 1
            elif str(reaction.emoji) == "🆓":
                not_guilty = reaction.count - 1

        if guilty >= not_guilty:
            sentence = random.choice(SENTENCES)
            await ctx.send(
                f"⚖️ **VERDICT: GUILTY** ⚖️\n"
                f"_{guilty} guilty — {not_guilty} not guilty_\n\n"
                f"**Sentence:** {sentence}"
            )
        else:
            await ctx.send(
                f"⚖️ **VERDICT: NOT GUILTY** ⚖️\n"
                f"_{not_guilty} not guilty — {guilty} guilty_\n\n"
                f"Donovan walks free today. Don't worry, he'll embarrass himself again soon enough."
            )
    except Exception as e:
        print(f"[ERROR] Trial failed: {e}")
        await ctx.send("The trial collapsed due to Donovan's overwhelming incompetence. Court dismissed.")
    finally:
        trial_active = False


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
