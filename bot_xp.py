import os
import discord
from discord.ext import commands, tasks
import sqlite3
import time

TOKEN = os.getenv("TOKEN")

TEXT_POINTS = 2
TEXT_COOLDOWN = 30

VC_POINTS = 5
VC_INTERVAL = 180  # 3 minuty

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
    cursor.execute(
        "INSERT OR IGNORE INTO points (user_id, guild_id) VALUES (?, ?)",
        (user_id, guild_id)
    )
    cursor.execute("""
        UPDATE points
        SET text = text + ?,
            voice = voice + ?,
            total = total + ?
        WHERE user_id = ? AND guild_id = ?
    """, (text, voice, text + voice, user_id, guild_id))
    conn.commit()


def get_points(user_id, guild_id):
    cursor.execute("""
        SELECT text, voice, total
        FROM points
        WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    return cursor.fetchone()


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
        if (member.guild.id, member.id) not in vc_times:
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
            gained_points = intervals * VC_POINTS

            add_points(user_id, guild_id, voice=gained_points)

            # przesuwamy licznik o dokładnie tyle interwałów ile weszło
            vc_times[(guild_id, user_id)] = start + (intervals * VC_INTERVAL)


@vc_loop.before_loop
async def before_vc_loop():
    await bot.wait_until_ready()


@bot.command(name="punkty")
async def punkty(ctx):
    if ctx.guild is None:
        await ctx.send("Ta komenda działa tylko na serwerze.")
        return

    row = get_points(ctx.author.id, ctx.guild.id)

    if row is None:
        await ctx.send(f"🏆 {ctx.author.mention}, nie masz jeszcze żadnych punktów.")
        return

    text_points, voice_points, total_points = row

    embed = discord.Embed(
        title="🏆 Twoje punkty",
        color=discord.Color.blurple()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(text_points), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(voice_points), inline=False)
    embed.add_field(name="⭐ Razem", value=str(total_points), inline=False)

    await ctx.send(embed=embed)


@bot.command(name="punkty_uzytkownika")
async def punkty_uzytkownika(ctx, member: discord.Member):
    if ctx.guild is None:
        await ctx.send("Ta komenda działa tylko na serwerze.")
        return

    row = get_points(member.id, ctx.guild.id)

    if row is None:
        await ctx.send(f"🏆 {member.mention} nie ma jeszcze żadnych punktów.")
        return

    text_points, voice_points, total_points = row

    embed = discord.Embed(
        title=f"🏆 Punkty użytkownika: {member.display_name}",
        color=discord.Color.green()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(text_points), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(voice_points), inline=False)
    embed.add_field(name="⭐ Razem", value=str(total_points), inline=False)

    await ctx.send(embed=embed)


@bot.command(name="ranking")
async def ranking(ctx):
    if ctx.guild is None:
        await ctx.send("Ta komenda działa tylko na serwerze.")
        return

    cursor.execute("""
        SELECT user_id, text, voice, total
        FROM points
        WHERE guild_id = ?
        ORDER BY total DESC
        LIMIT 10
    """, (ctx.guild.id,))
    rows = cursor.fetchall()

    if not rows:
        await ctx.send("Na tym serwerze nikt nie ma jeszcze punktów.")
        return

    embed = discord.Embed(
        title="🏆 Ranking serwera",
        color=discord.Color.gold()
    )

    lines = []
    for i, row in enumerate(rows, start=1):
        user_id, text_points, voice_points, total_points = row
        member = ctx.guild.get_member(user_id)

        if member:
            name = member.display_name
        else:
            name = f"Użytkownik {user_id}"

        lines.append(
            f"**{i}.** {name} — **{total_points} pkt** "
            f"(💬 {text_points} | 🎤 {voice_points})"
        )

    embed.description = "\n".join(lines)
    await ctx.send(embed=embed)


@bot.command(name="xpinfo")
async def xpinfo(ctx):
    embed = discord.Embed(
        title="📘 Zasady punktów",
        color=discord.Color.orange()
    )
    embed.add_field(name="💬 Wiadomości", value="2 punkty za wiadomość", inline=False)
    embed.add_field(name="⏳ Cooldown wiadomości", value="30 sekund", inline=False)
    embed.add_field(name="🎤 VC", value="5 punktów za 3 minuty", inline=False)
    embed.add_field(
        name="❌ Punkty VC nie lecą gdy",
        value="bot / mute / deaf / kanał AFK",
        inline=False
    )
    await ctx.send(embed=embed)


@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

    # złapanie osób już siedzących na VC po restarcie bota
    for guild in bot.guilds:
        for member in guild.members:
            if is_active(member):
                vc_times[(guild.id, member.id)] = time.time()

    if not vc_loop.is_running():
        vc_loop.start()


bot.run(TOKEN)
