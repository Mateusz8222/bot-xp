import os
import discord
from discord.ext import commands, tasks
import sqlite3
import time

TOKEN = os.getenv("TOKEN")

TEXT_POINTS = 2
TEXT_COOLDOWN = 30

VC_POINTS = 5
VC_INTERVAL = 180

conn = sqlite3.connect("xp.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS points (
    user_id INTEGER,
    guild_id INTEGER,
    text INTEGER DEFAULT 0,
    voice INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, guild_id)
)
""")
conn.commit()

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

cooldowns = {}
vc_times = {}

def add_points(user_id, guild_id, text=0, voice=0):
    cursor.execute("INSERT OR IGNORE INTO points (user_id, guild_id) VALUES (?, ?)", (user_id, guild_id))
    cursor.execute("""
    UPDATE points SET
    text = text + ?,
    voice = voice + ?,
    total = total + ?
    WHERE user_id = ? AND guild_id = ?
    """, (text, voice, text + voice, user_id, guild_id))
    conn.commit()

def is_active(member):
    if member.bot:
        return False
    if not member.voice or not member.voice.channel:
        return False

    v = member.voice

    if v.self_mute or v.mute:
        return False
    if v.self_deaf or v.deaf:
        return False

    if member.guild.afk_channel and v.channel == member.guild.afk_channel:
        return False

    return True

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    now = time.time()
    key = (message.guild.id, message.author.id)

    if key not in cooldowns or now - cooldowns[key] >= TEXT_COOLDOWN:
        add_points(message.author.id, message.guild.id, text=TEXT_POINTS)
        cooldowns[key] = now

    await bot.process_commands(message)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    if is_active(member):
        vc_times[(member.guild.id, member.id)] = time.time()
    else:
        vc_times.pop((member.guild.id, member.id), None)

@tasks.loop(seconds=60)
async def vc_loop():
    now = time.time()

    for (guild_id, user_id), start in list(vc_times.items()):
        guild = bot.get_guild(guild_id)
        if guild is None:
            vc_times.pop((guild_id, user_id), None)
            continue

        member = guild.get_member(user_id)

        if not member or not is_active(member):
            vc_times.pop((guild_id, user_id), None)
            continue

        elapsed = now - start

        if elapsed >= VC_INTERVAL:
            intervals = int(elapsed // VC_INTERVAL)
            add_points(user_id, guild_id, voice=intervals * VC_POINTS)
            vc_times[(guild_id, user_id)] = now

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    if not vc_loop.is_running():
        vc_loop.start()

bot.run(TOKEN)
