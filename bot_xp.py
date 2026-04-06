import os
import time
import sqlite3
import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("TOKEN")

# =========================
# USTAWIENIA XP
# =========================
TEXT_POINTS = 2
TEXT_MESSAGES_REQUIRED = 10

VC_POINTS_SOLO = 5
VC_POINTS_BONUS = 10
VC_INTERVAL = 600  # 10 minut = 600 sekund

DB_FILE = "xp.db"

# =========================
# BAZA DANYCH
# =========================
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS points (
    user_id INTEGER,
    guild_id INTEGER,
    text INTEGER DEFAULT 0,
    voice INTEGER DEFAULT 0,
    total INTEGER DEFAULT 0,
    message_count INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, guild_id)
)
""")
conn.commit()

# sprawdzenie czy kolumna message_count istnieje
cursor.execute("PRAGMA table_info(points)")
columns = [row[1] for row in cursor.fetchall()]
if "message_count" not in columns:
    cursor.execute("ALTER TABLE points ADD COLUMN message_count INTEGER DEFAULT 0")
    conn.commit()

# =========================
# BOT
# =========================
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)

# (guild_id, user_id) -> timestamp startu aktywnego VC
vc_times = {}


# =========================
# FUNKCJE BAZY
# =========================
def ensure_user(user_id: int, guild_id: int):
    cursor.execute(
        "INSERT OR IGNORE INTO points (user_id, guild_id) VALUES (?, ?)",
        (user_id, guild_id)
    )
    conn.commit()


def add_points(user_id: int, guild_id: int, text: int = 0, voice: int = 0):
    ensure_user(user_id, guild_id)
    cursor.execute("""
        UPDATE points
        SET text = text + ?,
            voice = voice + ?,
            total = total + ?
        WHERE user_id = ? AND guild_id = ?
    """, (text, voice, text + voice, user_id, guild_id))
    conn.commit()


def add_message_and_check_reward(user_id: int, guild_id: int) -> bool:
    ensure_user(user_id, guild_id)

    cursor.execute("""
        UPDATE points
        SET message_count = message_count + 1
        WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    conn.commit()

    cursor.execute("""
        SELECT message_count
        FROM points
        WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    row = cursor.fetchone()

    if row is None:
        return False

    message_count = row[0]

    if message_count % TEXT_MESSAGES_REQUIRED == 0:
        add_points(user_id, guild_id, text=TEXT_POINTS)
        return True

    return False


def get_points(user_id: int, guild_id: int):
    cursor.execute("""
        SELECT text, voice, total, message_count
        FROM points
        WHERE user_id = ? AND guild_id = ?
    """, (user_id, guild_id))
    return cursor.fetchone()


# =========================
# FUNKCJE VC
# =========================
def is_active(member: discord.Member) -> bool:
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


def count_active_members_in_channel(channel: discord.VoiceChannel) -> int:
    active_count = 0

    for member in channel.members:
        if member.bot:
            continue

        if not member.voice or not member.voice.channel:
            continue

        v = member.voice

        if v.self_mute or v.mute:
            continue

        if v.self_deaf or v.deaf:
            continue

        if member.guild.afk_channel and v.channel == member.guild.afk_channel:
            continue

        active_count += 1

    return active_count


# =========================
# EVENTY
# =========================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.guild is None:
        return

    if not message.content or not message.content.strip():
        return

    add_message_and_check_reward(message.author.id, message.guild.id)

    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    if member.bot:
        return

    key = (member.guild.id, member.id)

    if is_active(member):
        if key not in vc_times:
            vc_times[key] = time.time()
    else:
        vc_times.pop(key, None)


# =========================
# PĘTLA VC
# =========================
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

            if member.voice is None or member.voice.channel is None:
                vc_times.pop((guild_id, user_id), None)
                continue

            active_count = count_active_members_in_channel(member.voice.channel)

            if active_count >= 2:
                points_per_interval = VC_POINTS_BONUS
            else:
                points_per_interval = VC_POINTS_SOLO

            gained_points = intervals * points_per_interval
            add_points(user_id, guild_id, voice=gained_points)

            # przesunięcie licznika dokładnie o liczbę pełnych interwałów
            vc_times[(guild_id, user_id)] = start + (intervals * VC_INTERVAL)


@vc_loop.before_loop
async def before_vc_loop():
    await bot.wait_until_ready()


# =========================
# KOMENDY SLASH
# =========================
@bot.tree.command(name="punkty", description="Pokazuje Twoje punkty")
async def punkty(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    row = get_points(interaction.user.id, interaction.guild.id)

    if row is None:
        await interaction.response.send_message("Nie masz jeszcze żadnych punktów.", ephemeral=True)
        return

    text_points, voice_points, total_points, message_count = row

    embed = discord.Embed(
        title="🏆 Twoje punkty",
        color=discord.Color.blurple()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(text_points), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(voice_points), inline=False)
    embed.add_field(name="⭐ Razem", value=str(total_points), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(message_count), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="punkty_uzytkownika", description="Pokazuje punkty wybranej osoby")
@app_commands.describe(uzytkownik="Wybierz użytkownika")
async def punkty_uzytkownika(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    row = get_points(uzytkownik.id, interaction.guild.id)

    if row is None:
        await interaction.response.send_message(
            f"{uzytkownik.display_name} nie ma jeszcze punktów.",
            ephemeral=True
        )
        return

    text_points, voice_points, total_points, message_count = row

    embed = discord.Embed(
        title=f"🏆 Punkty użytkownika: {uzytkownik.display_name}",
        color=discord.Color.green()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(text_points), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(voice_points), inline=False)
    embed.add_field(name="⭐ Razem", value=str(total_points), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(message_count), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ranking", description="Pokazuje ranking serwera")
async def ranking(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    cursor.execute("""
        SELECT user_id, text, voice, total, message_count
        FROM points
        WHERE guild_id = ?
        ORDER BY total DESC, voice DESC, text DESC
        LIMIT 10
    """, (interaction.guild.id,))
    rows = cursor.fetchall()

    if not rows:
        await interaction.response.send_message(
            "Na tym serwerze nikt nie ma jeszcze punktów.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="🏆 Ranking serwera",
        color=discord.Color.gold()
    )

    lines = []
    for i, row in enumerate(rows, start=1):
        user_id, text_points, voice_points, total_points, message_count = row
        member = interaction.guild.get_member(user_id)
        name = member.display_name if member else f"Użytkownik {user_id}"

        lines.append(
            f"**{i}.** {name} — **{total_points} pkt** "
            f"(💬 {text_points} | 🎤 {voice_points} | 📝 {message_count})"
        )

    embed.description = "\n".join(lines)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="xpinfo", description="Pokazuje zasady punktów")
async def xpinfo(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📘 Zasady punktów",
        color=discord.Color.orange()
    )
    embed.add_field(name="💬 Wiadomości", value="2 punkty za każde 10 wiadomości", inline=False)
    embed.add_field(
        name="🎤 VC",
        value="5 punktów za 10 minut solo\n10 punktów za 10 minut z aktywną osobą",
        inline=False
    )
    embed.add_field(
        name="❌ Punkty VC nie lecą gdy",
        value="bot / mute / deaf / kanał AFK",
        inline=False
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)


# =========================
# READY
# =========================
@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

    # złapanie osób już siedzących na VC po restarcie
    for guild in bot.guilds:
        for member in guild.members:
            if is_active(member):
                vc_times[(guild.id, member.id)] = time.time()

    if not vc_loop.is_running():
        vc_loop.start()

    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print(f"Błąd synchronizacji komend: {e}")


# =========================
# START
# =========================
if not TOKEN:
    raise RuntimeError("Brak zmiennej TOKEN w Railway.")

bot.run(TOKEN)
