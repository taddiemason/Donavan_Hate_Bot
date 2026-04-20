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
DONOVAN_USERNAMES = {"itsrebrand", "streamerweiner"}
ROAST_CHANNEL_ID = int(os.getenv("ROAST_CHANNEL_ID", 0))
VOICE_CHANNEL_ID = int(os.getenv("VOICE_CHANNEL_ID", 0))
INSURANCE_COST_PER_MINUTE = 10
MAX_INSURANCE_MINUTES = 30

SHOP_ITEMS = {
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
    "slow_clap": {
        "name": "Slow Clap",
        "cost": 75,
        "description": "HateBot reacts to Donovan's next message with a series of 👏 emojis",
    },
    "receipt": {
        "name": "Receipt",
        "cost": 80,
        "description": "HateBot digs up and quotes one of his old messages alongside the roast",
    },
    "laugh_track": {
        "name": "Laugh Track",
        "cost": 90,
        "description": "Next roast is followed by 😂 spam from the bot",
    },
    "double_roast": {
        "name": "Double Roast",
        "cost": 100,
        "description": "Your next @mention fires TWO roasts back to back",
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
    "mega_roast": {
        "name": "Mega Roast",
        "cost": 200,
        "description": "Your next @mention also triggers an AI-generated extra savage bonus roast",
    },
    "press_release": {
        "name": "Press Release",
        "cost": 225,
        "description": "AI generates a fake formal press release announcing his latest L",
    },
    "hall_of_shame": {
        "name": "Hall of Shame",
        "cost": 250,
        "description": "Next roast gets pinned in the channel permanently",
    },
    "breaking_news": {
        "name": "Breaking News",
        "cost": 250,
        "description": "Bot posts a fake breaking news alert about him",
    },
    "intervention": {
        "name": "Intervention",
        "cost": 275,
        "description": "Bot @everyone and announces a formal server intervention for his behavior",
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
        "description": "Timeouts Donovan in the server for 60 seconds",
    },
    "lore_drop": {
        "name": "Lore Drop",
        "cost": 400,
        "description": "AI generates a full absurd origin story for why Donovan is the way he is",
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
trivia_active = False
trivia_answer = None
guessroast_active = False
highlow_games = {}

SLOT_SYMBOLS = ["🍋", "🍒", "🍇", "💎", "🎰", "7️⃣"]
SLOT_PAYOUTS = {("7️⃣", "7️⃣", "7️⃣"): 50, ("💎", "💎", "💎"): 25, ("🎰", "🎰", "🎰"): 15}

SERVER_ROAST_MILESTONES = {100: 50, 250: 75, 500: 100, 1000: 200, 2500: 300, 5000: 500}

TRIVIA_QUESTIONS = [
    {"q": "What fast food item does Donovan famously defend as underrated?", "a": "big mac"},
    {"q": "What game does Donovan always blame his deaths on?", "a": "rust"},
    {"q": "What is always stuck to Donovan's ass?", "a": "burger wrappers"},
    {"q": "What is the capital of France?", "a": "paris"},
    {"q": "How many sides does a hexagon have?", "a": "6"},
    {"q": "What year did the first iPhone launch?", "a": "2007"},
    {"q": "What planet is known as the Red Planet?", "a": "mars"},
    {"q": "What is the chemical symbol for gold?", "a": "au"},
    {"q": "How many players are on a basketball team on the court at once?", "a": "5"},
    {"q": "What is the largest ocean on Earth?", "a": "pacific"},
    {"q": "What year did World of Warcraft originally launch?", "a": "2004"},
    {"q": "How many strings does a standard guitar have?", "a": "6"},
    {"q": "What is 7 multiplied by 8?", "a": "56"},
    {"q": "What country is home to the kangaroo?", "a": "australia"},
    {"q": "What is the hardest natural substance on Earth?", "a": "diamond"},
]

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


DONOVAN_STOCK_BASE = 100.0
USER_STOCK_BASE = 10.0


def get_stocks():
    eco = load_economy()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return eco.get("stocks", {
        "donovan": {"price": DONOVAN_STOCK_BASE, "prev_price": DONOVAN_STOCK_BASE, "last_updated": now},
        "users": {},
    })


def save_stocks(stocks):
    eco = load_economy()
    eco["stocks"] = stocks
    save_economy(eco)


def get_display_prices(stocks):
    """Apply time-based drift without persisting — Donovan recovers slowly, users decay slowly."""
    now = datetime.datetime.now(datetime.timezone.utc)

    don = stocks["donovan"]
    hours = (now - datetime.datetime.fromisoformat(don["last_updated"])).total_seconds() / 3600
    don_price = min(don["price"] + hours * 0.25, DONOVAN_STOCK_BASE)

    user_prices = {}
    for uid, data in stocks.get("users", {}).items():
        hours = (now - datetime.datetime.fromisoformat(data["last_updated"])).total_seconds() / 3600
        user_prices[uid] = max(data["price"] - hours * 0.1, 1.0)

    return round(don_price, 2), {k: round(v, 2) for k, v in user_prices.items()}


def update_stocks_on_roast(user_id):
    stocks = get_stocks()
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    drop = round(random.uniform(1.5, 3.5), 2)
    stocks["donovan"]["prev_price"] = stocks["donovan"]["price"]
    stocks["donovan"]["price"] = max(round(stocks["donovan"]["price"] - drop, 2), 0.01)
    stocks["donovan"]["last_updated"] = now

    uid = str(user_id)
    if uid not in stocks.setdefault("users", {}):
        stocks["users"][uid] = {"price": USER_STOCK_BASE, "prev_price": USER_STOCK_BASE, "last_updated": now}
    gain = round(random.uniform(0.5, 2.0), 2)
    stocks["users"][uid]["prev_price"] = stocks["users"][uid]["price"]
    stocks["users"][uid]["price"] = round(stocks["users"][uid]["price"] + gain, 2)
    stocks["users"][uid]["last_updated"] = now

    save_stocks(stocks)


def save_count(count):
    with open(COUNTER_FILE, "w") as f:
        json.dump({"count": count}, f)


def load_economy():
    if os.path.exists(ECONOMY_FILE):
        with open(ECONOMY_FILE, "r") as f:
            return json.load(f)
    return {"balances": {}, "bounties": [], "insurance_expires": None,
            "pending_upgrades": {}, "inventory": {}, "market_listings": [],
            "slow_clap_pending": 0,
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


def is_double_coin_day():
    day = datetime.datetime.now(ZoneInfo("America/New_York")).weekday()
    return day in (4, 5, 6)  # Friday, Saturday, Sunday


def get_daily_reward(streak):
    base = 25 + (min(streak, 30) - 1) * 5
    if streak % 7 == 0:
        base *= 2
    return base


def is_donovan(user):
    return user.name.lower() in DONOVAN_USERNAMES


def get_donovan_activity(guild):
    for member in guild.members:
        if member.name.lower() in DONOVAN_USERNAMES:
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
    for member in guild.members:
        if member.name.lower() in DONOVAN_USERNAMES and member.voice:
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

    # Weekly lottery drawing
    eco = load_economy()
    tickets = eco.get("lottery_tickets", {})
    pot = eco.get("lottery_pot", 0)
    if tickets and pot > 0:
        pool = []
        for uid, count in tickets.items():
            pool.extend([uid] * count)
        winner_id = random.choice(pool)
        winner = channel.guild.get_member(int(winner_id))
        winner_name = winner.display_name if winner else "Someone"
        add_coins(int(winner_id), pot)
        eco["lottery_tickets"] = {}
        eco["lottery_pot"] = 0
        save_economy(eco)
        await channel.send(
            f"🎟️ **WEEKLY LOTTERY DRAWING!**\n\n"
            f"Out of {len(pool)} tickets...\n"
            f"🏆 **{winner_name}** wins the **{pot} coin** pot!\n"
            f"New lottery starts now. Buy tickets with `!lottery <amount>`."
        )
    else:
        eco["lottery_tickets"] = {}
        eco["lottery_pot"] = 0
        save_economy(eco)


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

    # First message of the day bonus
    today = datetime.date.today().isoformat()
    eco = load_economy()
    if eco.get("first_message_today") != today:
        eco["first_message_today"] = today
        save_economy(eco)
        bonus = 30 if is_double_coin_day() else 15
        add_coins(message.author.id, bonus)
        await message.channel.send(f"🌅 {message.author.mention} sent the first message of the day! **+{bonus} coins!**")

    # Higher or lower game responses
    if message.author.id in highlow_games:
        game = highlow_games[message.author.id]
        if message.channel.id == game["channel_id"]:
            content = message.content.lower().strip()
            if content in ("higher", "lower"):
                new_num = random.randint(1, 100)
                old_num = game["number"]
                correct = (content == "higher" and new_num > old_num) or (content == "lower" and new_num < old_num)
                if new_num == old_num:
                    await message.channel.send(f"🎯 It's **{new_num}** — a tie! Keep going.")
                elif correct:
                    game["multiplier"] += 1
                    game["number"] = new_num
                    await message.channel.send(f"✅ **{new_num}!** Correct! Multiplier: **{game['multiplier']}x** — type `higher`, `lower`, or `cashout`.")
                else:
                    bet = game["bet"]
                    del highlow_games[message.author.id]
                    await message.channel.send(f"❌ **{new_num}!** Wrong! You lost **{bet} coins**.")
            elif content == "cashout":
                winnings = game["bet"] * game["multiplier"]
                add_coins(message.author.id, winnings)
                del highlow_games[message.author.id]
                await message.channel.send(f"💰 Cashed out at **{game['multiplier']}x**! You won **{winnings} coins**!")

    # Trivia answer check
    if trivia_active and trivia_answer and not message.author.bot:
        if trivia_answer.lower() in message.content.lower():
            globals()["trivia_active"] = False
            reward = 50
            add_coins(message.author.id, reward)
            await message.channel.send(f"✅ {message.author.mention} got it! The answer was **{trivia_answer}**. **+{reward} coins!**")

    # Guess the roast answer check
    if guessroast_active and not message.author.bot:
        if "donovan" in message.content.lower():
            globals()["guessroast_active"] = False
            add_coins(message.author.id, 30)
            await message.channel.send(f"✅ {message.author.mention} got it! It was **Donovan** (obviously). **+30 coins!**")

    bot_member = message.guild.get_member(bot.user.id)
    bot_mentioned = bot.user in message.mentions or (
        bot_member and any(role in message.role_mentions for role in bot_member.roles)
    )

    if is_donovan(message.author):
        add_coins(message.author.id, 1)
        eco = load_economy()
        if eco.get("slow_clap_pending", 0) > 0:
            eco["slow_clap_pending"] -= 1
            save_economy(eco)
            for _ in range(5):
                await message.add_reaction("👏")

    if is_donovan(message.author) and len(message.content) > 10:
        if await is_hot_take(message.content):
            flagged = await message.reply(
                "🚨 **HOT TAKE ALERT** 🚨\nDonovan is at it again. React to cast your vote:"
            )
            await flagged.add_reaction("🔥")
            await flagged.add_reaction("🧊")

    if bot_mentioned:
        try:
            if is_donovan(message.author):
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
                donovan = discord.utils.find(lambda m: m.name.lower() in DONOVAN_USERNAMES, message.guild.members)
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

            if consume_upgrade(message.author.id, "laugh_track"):
                await message.channel.send("😂😂😂😂😂😂😂😂😂😂")

            if consume_upgrade(message.author.id, "receipt"):
                try:
                    async for old_msg in message.channel.history(limit=200):
                        if old_msg.author.name.lower() in DONOVAN_USERNAMES and len(old_msg.content) > 15 and old_msg.id != message.id:
                            await message.channel.send(f"🧾 **RECEIPT:** _{old_msg.author.display_name} once said:_ \"{old_msg.content}\"")
                            break
                except Exception:
                    pass

            if consume_upgrade(message.author.id, "press_release"):
                pr = await ask_openai(f"Write a short fake formal press release (3-4 sentences) from 'Donovan Industries' announcing his latest embarrassing L. Make it sound official but absurd.")
                await message.channel.send(f"📰 **PRESS RELEASE:**\n{pr}")

            if consume_upgrade(message.author.id, "breaking_news"):
                news = await ask_openai("Write a fake breaking news alert (1-2 sentences, all caps headline) about Donovan doing something embarrassing or pathetic. Include a fake news network name.")
                await message.channel.send(f"🚨 **BREAKING NEWS** 🚨\n{news}")

            if consume_upgrade(message.author.id, "intervention"):
                await message.channel.send(f"@everyone\n\n📢 **FORMAL SERVER INTERVENTION**\n\nThis server has come together to formally address Donovan's ongoing behaviour. We are concerned. We are united. And we are not impressed.\n\nPlease take this moment to reflect, Donovan.")

            if consume_upgrade(message.author.id, "lore_drop"):
                lore = await ask_openai("Write a short absurd fictional origin story (3-5 sentences) for why Donovan is the way he is. Make it ridiculous, creative, and savage.")
                await message.channel.send(f"📖 **DONOVAN LORE DROP:**\n{lore}")

            if consume_upgrade(message.author.id, "mega_roast"):
                mega = await ask_openai("Give the most savage, creative, brutal roast about Donovan you can. Go all out.")
                await message.channel.send(f"💥 **MEGA ROAST:** {mega}")

            if consume_upgrade(message.author.id, "scorched_earth"):
                for i in range(3):
                    roast = await ask_openai(f"Give a unique savage roast about Donovan. Make it different each time. Roast #{i+1}.")
                    await message.channel.send(f"🔥 {roast}")

            if consume_upgrade(message.author.id, "exile"):
                donovan = discord.utils.find(lambda m: m.name.lower() in DONOVAN_USERNAMES, message.guild.members)
                if donovan:
                    try:
                        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=60)
                        await donovan.timeout(until, reason="Exile purchased by the people.")
                        await message.channel.send("⛔ Donovan has been exiled for 60 seconds. Enjoy the peace.")
                    except Exception:
                        await message.channel.send("⛔ Exile failed — bot needs Moderate Members permission.")

            coin_reward = 20 if is_double_coin_day() else 10
            if is_double_coin_day():
                await message.channel.send("💰 **2x Roast Coins** — Fuck Donovan Friday/Weekend bonus active!")
            add_coins(message.author.id, coin_reward)
            update_stocks_on_roast(message.author.id)
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

            eco = load_economy()
            milestones_given = eco.get("server_milestones_given", [])
            if count in SERVER_ROAST_MILESTONES and count not in milestones_given:
                milestones_given.append(count)
                eco["server_milestones_given"] = milestones_given
                save_economy(eco)
                bonus = SERVER_ROAST_MILESTONES[count]
                for member in message.guild.members:
                    if not member.bot:
                        add_coins(member.id, bonus)
                await message.channel.send(
                    f"🎉 **SERVER MILESTONE: {count} total roasts!**\n"
                    f"Everyone gets **+{bonus} Roast Coins** for their dedication to roasting Donovan!"
                )
        except Exception as e:
            print(f"[ERROR] on_message crashed: {e}")
            await message.channel.send(random.choice(GENERAL_ROASTS))

    await bot.process_commands(message)


@bot.command(name="daily")
async def daily_checkin(ctx):
    eco = load_economy()
    uid = str(ctx.author.id)
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    data = eco.setdefault("daily_checkins", {}).get(uid, {"last_checkin": None, "streak": 0})

    if data["last_checkin"] == today:
        await ctx.send("You've already checked in today. Come back tomorrow.")
        return

    streak = data["streak"] + 1 if data["last_checkin"] == yesterday else 1
    reward = get_daily_reward(streak)
    if is_double_coin_day():
        reward *= 2

    eco["daily_checkins"][uid] = {"last_checkin": today, "streak": streak}
    save_economy(eco)
    add_coins(ctx.author.id, reward)

    streak_msg = f" 🔥 **{streak} day streak!**" if streak > 1 else ""
    milestone_msg = " 🎉 **7-DAY BONUS — DOUBLED!**" if streak % 7 == 0 else ""
    double_msg = " 💰 **Weekend 2x active!**" if is_double_coin_day() else ""
    await ctx.send(f"✅ Daily check-in! **+{reward} coins**{streak_msg}{milestone_msg}{double_msg}")


@bot.command(name="flip")
async def coinflip(ctx, amount: int = None, side: str = None):
    if not amount or not side or side.lower() not in ("heads", "tails"):
        await ctx.send("Usage: `!flip <amount> heads` or `!flip <amount> tails`")
        return
    if amount <= 0:
        await ctx.send("Bet must be positive.")
        return
    if not spend_coins(ctx.author.id, amount):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**.")
        return
    result = random.choice(["heads", "tails"])
    if result == side.lower():
        add_coins(ctx.author.id, amount * 2)
        await ctx.send(f"🪙 **{result.upper()}!** You won **{amount} coins!**")
    else:
        await ctx.send(f"🪙 **{result.upper()}!** You lost **{amount} coins**. Better luck next time.")


@bot.command(name="slots")
async def slots(ctx, amount: int = None):
    if not amount or amount <= 0:
        await ctx.send("Usage: `!slots <amount>`")
        return
    if not spend_coins(ctx.author.id, amount):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**.")
        return
    reels = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
    display = " | ".join(reels)
    key = tuple(reels)
    mult = SLOT_PAYOUTS.get(key, 0)
    if mult == 0:
        if reels[0] == reels[1] == reels[2]:
            mult = 10
        elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
            mult = 2
    if mult > 0:
        winnings = amount * mult
        add_coins(ctx.author.id, winnings)
        await ctx.send(f"🎰 [ {display} ]\n**{mult}x PAYOUT!** You won **{winnings} coins!**")
    else:
        await ctx.send(f"🎰 [ {display} ]\nNo match. You lost **{amount} coins**.")


@bot.command(name="trivia")
async def trivia(ctx):
    global trivia_active, trivia_answer
    if trivia_active:
        await ctx.send("A trivia question is already active!")
        return
    trivia_active = True
    q = random.choice(TRIVIA_QUESTIONS)
    trivia_answer = q["a"]
    await ctx.send(f"🧠 **TRIVIA** — First to answer wins **50 coins!**\n\n_{q['q']}_\n\nYou have 30 seconds!")
    await asyncio.sleep(30)
    if trivia_active:
        trivia_active = False
        trivia_answer = None
        await ctx.send(f"⏱️ Time's up! The answer was **{q['a']}**.")


@bot.command(name="guessroast")
async def guess_roast(ctx):
    global guessroast_active
    if guessroast_active:
        await ctx.send("A guess the roast game is already active!")
        return
    guessroast_active = True
    all_roasts = GENERAL_ROASTS + RUST_ROASTS + WOW_ROASTS
    roast = random.choice(all_roasts)
    blanked = roast.replace("Donovan", "**[???]**").replace("donovan", "**[???]**")
    await ctx.send(f"🎭 **GUESS WHO THIS ROAST IS AIMED AT:**\n\n_{blanked}_\n\nFirst to type the name wins **30 coins!** (20 seconds)")
    await asyncio.sleep(20)
    if guessroast_active:
        guessroast_active = False
        await ctx.send("⏱️ Time's up! It was **Donovan**. Obviously.")


@bot.command(name="highlow")
async def highlow(ctx, amount: int = None):
    if not amount or amount <= 0:
        await ctx.send("Usage: `!highlow <amount>`")
        return
    if ctx.author.id in highlow_games:
        await ctx.send("You already have a game in progress! Type `higher`, `lower`, or `cashout`.")
        return
    if not spend_coins(ctx.author.id, amount):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**.")
        return
    number = random.randint(1, 100)
    highlow_games[ctx.author.id] = {"number": number, "bet": amount, "multiplier": 1, "channel_id": ctx.channel.id}
    await ctx.send(f"🎯 The number is **{number}**.\nWill the next be `higher` or `lower`? Type your answer!\nType `cashout` to take your winnings at any time.")


@bot.command(name="lottery")
async def lottery(ctx, amount: int = None):
    if not amount or amount < 10:
        eco = load_economy()
        pot = eco.get("lottery_pot", 0)
        tickets = eco.get("lottery_tickets", {}).get(str(ctx.author.id), 0)
        await ctx.send(f"🎟️ **Weekly Lottery** — 10 coins per ticket\nCurrent pot: **{pot} coins** | Your tickets: **{tickets}**\nUsage: `!lottery <amount>` (must be multiple of 10)")
        return
    tickets = amount // 10
    cost = tickets * 10
    if not spend_coins(ctx.author.id, cost):
        bal = load_economy()["balances"].get(str(ctx.author.id), 0)
        await ctx.send(f"Not enough coins. You have **{bal}**.")
        return
    eco = load_economy()
    uid = str(ctx.author.id)
    eco.setdefault("lottery_tickets", {})[uid] = eco.get("lottery_tickets", {}).get(uid, 0) + tickets
    eco["lottery_pot"] = eco.get("lottery_pot", 0) + cost
    save_economy(eco)
    await ctx.send(f"🎟️ Bought **{tickets} ticket(s)** for **{cost} coins**! Pot is now **{eco['lottery_pot']} coins**. Drawing Sunday at 9 PM EST!")


@bot.command(name="stockmarket")
async def stock_market(ctx):
    stocks = get_stocks()
    don_price, user_prices = get_display_prices(stocks)

    don_prev = stocks["donovan"].get("prev_price", DONOVAN_STOCK_BASE)
    don_change = round(don_price - don_prev, 2)
    don_pct = round((don_change / don_prev * 100) if don_prev else 0, 1)
    don_trend = "📉" if don_change < 0 else "📈"

    lines = [
        "📊 **DONOVAN STOCK EXCHANGE**\n",
        f"**$DONOVAN** — ${don_price:.2f}   {don_trend} {don_change:+.2f} ({don_pct:+.1f}%)",
        f"_The lower it goes the better for all of us._\n",
    ]

    if user_prices:
        top = sorted(user_prices.items(), key=lambda x: x[1], reverse=True)[:5]
        lines.append("**Top Roasters:**")
        for uid, price in top:
            member = ctx.guild.get_member(int(uid))
            name = (member.display_name if member else "Unknown").upper()[:10]
            prev = stocks["users"].get(uid, {}).get("prev_price", USER_STOCK_BASE)
            change = round(price - prev, 2)
            pct = round((change / prev * 100) if prev else 0, 1)
            trend = "📈" if change >= 0 else "📉"
            lines.append(f"**${name}** — ${price:.2f}   {trend} {change:+.2f} ({pct:+.1f}%)")
    else:
        lines.append("_No roasters on the board yet. Start roasting to get listed._")

    await ctx.send("\n".join(lines))


@bot.command(name="Commands")
async def commands_list(ctx):
    await ctx.send(
        "**📋 Donovan Hate Bot — Commands (1/2)**\n\n"
        "**`@Donovan Hate Bot`** — Roasts Donovan. Ask it a question for a smart response.\n"
        "**`!Trial <reason>`** — Puts Donovan on trial. Server votes guilty/not guilty for 60 seconds.\n"
        "**`!Guesswhosaidit`** — 3 round game. Guess if the quote was Donovan or someone else.\n"
        "**`!TTS on/off`** — Toggles voice channel roasts. (Donovan cannot use this.)\n\n"
        "**💰 Economy**\n"
        "**`!balance`** — Check your Roast Coin balance.\n"
        "**`!leaderboard`** — Top 5 coin holders.\n"
        "**`!shop`** — View upgrades for sale.\n"
        "**`!buy <item>`** — Purchase an upgrade (goes to inventory).\n"
        "**`!inventory`** — View your owned and armed items.\n"
        "**`!use <item>`** — Arm an item from your inventory (fires on next @mention).\n"
        "**`!bounty <amount> <description>`** — Post a bounty paid to whoever triggers the next roast.\n"
        "**`!bounties`** — View active bounties.\n"
        "**`!insurance <minutes>`** — Donovan only: buy temporary (useless) protection.\n"
        "**`!give @user <amount>`** — Transfer coins to another member.\n"
        "**`!blackmarket`** — View peer-to-peer upgrade listings.\n"
        "**`!listitem <item> <price>`** — List an owned upgrade for sale.\n"
        "**`!stockmarket`** — View Donovan's tanking stock price and top roaster rankings."
    )
    await ctx.send(
        "**📋 Donovan Hate Bot — Commands (2/2)**\n\n"
        "**🎮 Minigames & Rewards**\n"
        "**`!daily`** — 25 coin daily check-in. Streak builds a multiplier, doubles at 7 days.\n"
        "**`!flip <amount> heads/tails`** — Coinflip gamble.\n"
        "**`!slots <amount>`** — Slot machine. Match symbols for big payouts.\n"
        "**`!trivia`** — First to answer wins 50 coins.\n"
        "**`!guessroast`** — Roast posted with name blanked, guess who it's about.\n"
        "**`!highlow <amount>`** — Guess higher or lower, chain correct answers for a multiplier.\n"
        "**`!lottery <amount>`** — Buy lottery tickets (10 coins each). Drawn every Sunday at 9 PM EST.\n"
        "**`!buyitem <id>`** — Buy an upgrade from the black market.\n\n"
        "**`!Commands`** — Shows this list."
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
    eco.setdefault("inventory", {}).setdefault(str(ctx.author.id), []).append(item_name.lower())
    save_economy(eco)
    await ctx.send(f"✅ Purchased **{item['name']}**! It's in your inventory. Use `!use {item_name.lower()}` when you're ready to arm it.")


@bot.command(name="inventory")
async def inventory(ctx, member: discord.Member = None):
    target = member or ctx.author
    eco = load_economy()
    owned = eco.get("inventory", {}).get(str(target.id), [])
    armed = eco.get("pending_upgrades", {}).get(str(target.id), [])
    if not owned and not armed:
        await ctx.send(f"**{target.display_name}** has no items. Buy some with `!shop`.")
        return
    lines = []
    if owned:
        lines.append("**Inventory (unequipped):**")
        for item in owned:
            lines.append(f"  • {SHOP_ITEMS[item]['name']} (`{item}`)")
    if armed:
        lines.append("**Armed (fires on next @mention):**")
        for item in armed:
            lines.append(f"  ⚡ {SHOP_ITEMS.get(item, {}).get('name', item)}")
    await ctx.send(f"🎒 **{target.display_name}'s Items**\n" + "\n".join(lines))


@bot.command(name="use")
async def use_item(ctx, item_name: str = None):
    if not item_name:
        await ctx.send("Usage: `!use <item_name>`")
        return
    item_name = item_name.lower()
    eco = load_economy()
    uid = str(ctx.author.id)
    owned = eco.get("inventory", {}).get(uid, [])
    if item_name not in owned:
        await ctx.send(f"You don't have a **{SHOP_ITEMS.get(item_name, {}).get('name', item_name)}** in your inventory.")
        return
    owned.remove(item_name)
    eco["inventory"][uid] = owned

    if item_name == "slow_clap":
        eco["slow_clap_pending"] = eco.get("slow_clap_pending", 0) + 1
        save_economy(eco)
        await ctx.send("👏 **Slow Clap** armed! It will fire on Donovan's next message.")
        return

    eco.setdefault("pending_upgrades", {}).setdefault(uid, []).append(item_name)
    save_economy(eco)
    item = SHOP_ITEMS[item_name]
    await ctx.send(f"⚡ **{item['name']}** armed! It will fire on your next @mention of the bot.")


@bot.command(name="bounty")
async def post_bounty(ctx, amount: int = None, *, description: str = None):
    if is_donovan(ctx.author):
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
    if not is_donovan(ctx.author):
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
    eco = load_economy()
    uid = str(ctx.author.id)
    owned = eco.get("inventory", {}).get(uid, [])
    if item_name not in owned:
        await ctx.send(f"You don't have a **{SHOP_ITEMS[item_name]['name']}** in your inventory to sell.")
        return
    owned.remove(item_name)
    eco["inventory"][uid] = owned
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
    eco.setdefault("inventory", {}).setdefault(str(ctx.author.id), []).append(listing["item"])
    save_economy(eco)
    seller = ctx.guild.get_member(int(listing["seller_id"]))
    seller_name = seller.display_name if seller else "Unknown"
    item_name = SHOP_ITEMS.get(listing["item"], {}).get("name", listing["item"])
    await ctx.send(f"🕶️ **{ctx.author.display_name}** bought **{item_name}** from **{seller_name}** for **{listing['price']} coins**.")


@bot.command(name="Guesswhosaidit")
async def guess_who(ctx):
    global guess_game_active

    if is_donovan(ctx.author):
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

    if is_donovan(ctx.author):
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

    if is_donovan(ctx.author):
        await ctx.send("Lmao no. You don't get a say in this, Donovan.")
        return

    if state is None or state.lower() not in ("on", "off"):
        await ctx.send(f"TTS is currently **{'on' if tts_enabled else 'off'}**. Use `!TTS on` or `!TTS off`.")
        return

    tts_enabled = state.lower() == "on"
    await ctx.send(f"TTS roasts turned **{state.lower()}**.")


bot.run(os.getenv("DISCORD_TOKEN"))
