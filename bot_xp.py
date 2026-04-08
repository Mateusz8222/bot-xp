import os
import time
import sqlite3
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

# =========================================================
# KONFIG
# =========================================================
TOKEN = os.getenv("TOKEN") or os.getenv("DISCORD_TOKEN")
DB_FILE = os.getenv("XP_DB_FILE", "xp.db")
LOG_FILE = os.getenv("XP_LOG_FILE", "xp_bot.log")

# =========================================================
# ID KANAŁÓW
# =========================================================
POINTS_CHANNEL_ID = 1490629053286191206      # 📊・sprawdz-punkty
RANKING_CHANNEL_ID = 1490629324305600594     # 🏆・ranking
XPINFO_CHANNEL_ID = 1490629632796524554      # 📘・info-xp
SHOP_CHANNEL_ID = 1490648124006338640        # 🛒・sklep

LEGEND_TEXT_CHANNEL_ID = 1490791025671803013 # 💎・legenda-czat
LEGEND_VC_CHANNEL_ID = 1490792255504646407   # 💎・Legenda VC

# =========================================================
# ID RÓL
# =========================================================
VIP_ROLE_ID = 1474567627895738388
LEGEND_ROLE_ID = 1490683484262498335

# =========================================================
# USTAWIENIA XP
# =========================================================
TEXT_MESSAGES_REQUIRED = 10
TEXT_POINTS = 2
TEXT_MIN_LENGTH = 4
TEXT_COOLDOWN_SECONDS = 12
TEXT_DUPLICATE_WINDOW_SECONDS = 180

VC_INTERVAL_SECONDS = 600  # 10 minut
VC_POINTS_SOLO = 5
VC_POINTS_WITH_ACTIVE = 10

VIP_MULTIPLIER = 1.20
LEGEND_MULTIPLIER = 1.40

DAILY_VOICE_CAP = 3000
DAILY_TEXT_CAP = 1000

# =========================================================
# POZIOMY / NAGRODY
# =========================================================
LEVEL_STEP = 1000
LEVEL_ROLE_REWARDS = {
    10: VIP_ROLE_ID,
    25: LEGEND_ROLE_ID,
}

# =========================================================
# SKLEP
# =========================================================
SHOP_ITEMS = {
    "vip": {
        "price": 50000,
        "role_id": VIP_ROLE_ID,
        "label": "⭐ VIP",
    },
    "legenda": {
        "price": 100000,
        "role_id": LEGEND_ROLE_ID,
        "label": "💎 LEGENDA",
    },
}

PANEL_CHANNELS = {
    "points": POINTS_CHANNEL_ID,
    "ranking": RANKING_CHANNEL_ID,
    "xpinfo": XPINFO_CHANNEL_ID,
    "shop": SHOP_CHANNEL_ID,
}

# =========================================================
# LOGOWANIE
# =========================================================
logger = logging.getLogger("xpbot")
logger.setLevel(logging.INFO)
logger.handlers.clear()

_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

_stream = logging.StreamHandler()
_stream.setFormatter(_formatter)
logger.addHandler(_stream)

_file = RotatingFileHandler(LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
_file.setFormatter(_formatter)
logger.addHandler(_file)

# =========================================================
# BAZA
# =========================================================
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_db() -> None:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS points (
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            text_points INTEGER NOT NULL DEFAULT 0,
            voice_points INTEGER NOT NULL DEFAULT 0,
            total_points INTEGER NOT NULL DEFAULT 0,
            message_count INTEGER NOT NULL DEFAULT 0,
            last_text_award_at REAL NOT NULL DEFAULT 0,
            last_vc_award_at REAL NOT NULL DEFAULT 0,
            daily_text_points INTEGER NOT NULL DEFAULT 0,
            daily_voice_points INTEGER NOT NULL DEFAULT 0,
            daily_reset_date TEXT NOT NULL DEFAULT '',
            PRIMARY KEY (guild_id, user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS panel_messages (
            guild_id INTEGER NOT NULL,
            panel_key TEXT NOT NULL,
            channel_id INTEGER NOT NULL,
            message_id INTEGER NOT NULL,
            PRIMARY KEY (guild_id, panel_key)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            guild_id INTEGER PRIMARY KEY,
            text_enabled INTEGER NOT NULL DEFAULT 1,
            voice_enabled INTEGER NOT NULL DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


def today_str() -> str:
    return time.strftime("%Y-%m-%d")


def ensure_user_row(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO points (
            guild_id, user_id, text_points, voice_points, total_points, message_count,
            last_text_award_at, last_vc_award_at, daily_text_points, daily_voice_points, daily_reset_date
        ) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, ?)
    """, (guild_id, user_id, today_str()))
    conn.commit()
    conn.close()


def ensure_daily_reset(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT daily_reset_date
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()
    if row and row["daily_reset_date"] != today_str():
        cur.execute("""
            UPDATE points
            SET daily_text_points = 0,
                daily_voice_points = 0,
                daily_reset_date = ?
            WHERE guild_id = ? AND user_id = ?
        """, (today_str(), guild_id, user_id))
        conn.commit()
    conn.close()


def get_points_row(guild_id: int, user_id: int) -> Optional[sqlite3.Row]:
    ensure_user_row(guild_id, user_id)
    ensure_daily_reset(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT text_points, voice_points, total_points, message_count,
               last_text_award_at, last_vc_award_at, daily_text_points, daily_voice_points
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()
    conn.close()
    return row


def update_message_count(guild_id: int, user_id: int) -> int:
    ensure_user_row(guild_id, user_id)
    ensure_daily_reset(guild_id, user_id)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET message_count = message_count + 1
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    cur.execute("""
        SELECT message_count
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    count = cur.fetchone()["message_count"]
    conn.commit()
    conn.close()
    return count


def add_points_db(guild_id: int, user_id: int, *, text_points: int = 0, voice_points: int = 0) -> None:
    ensure_user_row(guild_id, user_id)
    ensure_daily_reset(guild_id, user_id)
    total_add = max(0, text_points) + max(0, voice_points)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET text_points = text_points + ?,
            voice_points = voice_points + ?,
            total_points = total_points + ?,
            daily_text_points = daily_text_points + ?,
            daily_voice_points = daily_voice_points + ?,
            last_text_award_at = CASE WHEN ? > 0 THEN ? ELSE last_text_award_at END,
            last_vc_award_at = CASE WHEN ? > 0 THEN ? ELSE last_vc_award_at END
        WHERE guild_id = ? AND user_id = ?
    """, (
        max(0, text_points),
        max(0, voice_points),
        total_add,
        max(0, text_points),
        max(0, voice_points),
        1 if text_points > 0 else 0, time.time(),
        1 if voice_points > 0 else 0, time.time(),
        guild_id, user_id
    ))
    conn.commit()
    conn.close()


def add_total_points(guild_id: int, user_id: int, amount: int) -> None:
    if amount <= 0:
        return
    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET total_points = total_points + ?
        WHERE guild_id = ? AND user_id = ?
    """, (amount, guild_id, user_id))
    conn.commit()
    conn.close()


def remove_total_points(guild_id: int, user_id: int, amount: int) -> bool:
    if amount <= 0:
        return False

    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT total_points
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()
    if row is None or row["total_points"] < amount:
        conn.close()
        return False

    cur.execute("""
        UPDATE points
        SET total_points = total_points - ?
        WHERE guild_id = ? AND user_id = ?
    """, (amount, guild_id, user_id))
    conn.commit()
    conn.close()
    return True


def set_total_points(guild_id: int, user_id: int, amount: int) -> None:
    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET total_points = ?
        WHERE guild_id = ? AND user_id = ?
    """, (max(0, amount), guild_id, user_id))
    conn.commit()
    conn.close()


def get_top_users(guild_id: int, limit: int = 10) -> list[sqlite3.Row]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT user_id, text_points, voice_points, total_points, message_count
        FROM points
        WHERE guild_id = ?
        ORDER BY total_points DESC, voice_points DESC, text_points DESC
        LIMIT ?
    """, (guild_id, limit))
    rows = cur.fetchall()
    conn.close()
    return rows


def save_panel_message(guild_id: int, panel_key: str, channel_id: int, message_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR REPLACE INTO panel_messages (guild_id, panel_key, channel_id, message_id)
        VALUES (?, ?, ?, ?)
    """, (guild_id, panel_key, channel_id, message_id))
    conn.commit()
    conn.close()


def get_panel_message(guild_id: int, panel_key: str) -> Optional[sqlite3.Row]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT channel_id, message_id
        FROM panel_messages
        WHERE guild_id = ? AND panel_key = ?
    """, (guild_id, panel_key))
    row = cur.fetchone()
    conn.close()
    return row


def get_all_panel_messages(guild_id: int) -> list[sqlite3.Row]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT panel_key, channel_id, message_id
        FROM panel_messages
        WHERE guild_id = ?
    """, (guild_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


# =========================================================
# BOT
# =========================================================
class XPBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.messages = True
        intents.message_content = True
        intents.voice_states = True
        super().__init__(command_prefix="!", intents=intents)
        self.vc_active_since: dict[tuple[int, int], float] = {}
        self.last_message_award_check: dict[tuple[int, int], float] = {}
        self.last_message_signature: dict[tuple[int, int], tuple[str, float]] = {}

    async def setup_hook(self) -> None:
        self.add_view(ShopView(self))
        self.add_view(UtilityView(self))


bot = XPBot()

# =========================================================
# POMOCNICZE
# =========================================================
def safe_int(value: Optional[int]) -> int:
    return int(value or 0)


def calculate_level(total_points: int) -> int:
    return max(0, total_points // LEVEL_STEP)


def points_to_next_level(total_points: int) -> int:
    next_level = calculate_level(total_points) + 1
    return max(0, (next_level * LEVEL_STEP) - total_points)


def get_member_multiplier(member: discord.Member) -> float:
    role_ids = {role.id for role in member.roles}
    if LEGEND_ROLE_ID in role_ids:
        return LEGEND_MULTIPLIER
    if VIP_ROLE_ID in role_ids:
        return VIP_MULTIPLIER
    return 1.0


def get_rank_prefix(member: Optional[discord.Member]) -> str:
    if member is None:
        return ""
    role_ids = {role.id for role in member.roles}
    if LEGEND_ROLE_ID in role_ids:
        return "💎 "
    if VIP_ROLE_ID in role_ids:
        return "⭐ "
    return ""


def is_active_for_vc(member: discord.Member) -> bool:
    if member.bot:
        return False
    if member.voice is None or member.voice.channel is None:
        return False

    v = member.voice
    if v.self_mute or v.mute:
        return False
    if v.self_deaf or v.deaf:
        return False
    if member.guild.afk_channel and v.channel.id == member.guild.afk_channel.id:
        return False
    return True


def count_active_members_in_channel(channel: discord.VoiceChannel) -> int:
    return sum(1 for member in channel.members if is_active_for_vc(member))


def can_count_message(message: discord.Message) -> bool:
    if message.author.bot or message.guild is None:
        return False
    content = (message.content or "").strip()
    if len(content) < TEXT_MIN_LENGTH:
        return False

    key = (message.guild.id, message.author.id)
    now = time.time()

    last_time = bot.last_message_award_check.get(key, 0)
    if now - last_time < TEXT_COOLDOWN_SECONDS:
        return False

    last_content_info = bot.last_message_signature.get(key)
    lowered = content.lower()
    if last_content_info:
        last_content, last_when = last_content_info
        if lowered == last_content and (now - last_when) <= TEXT_DUPLICATE_WINDOW_SECONDS:
            return False

    bot.last_message_award_check[key] = now
    bot.last_message_signature[key] = (lowered, now)
    return True


def add_points_with_role_bonus(member: discord.Member, *, text_points: int = 0, voice_points: int = 0) -> tuple[int, int]:
    row = get_points_row(member.guild.id, member.id)
    daily_text = safe_int(row["daily_text_points"]) if row else 0
    daily_voice = safe_int(row["daily_voice_points"]) if row else 0

    multiplier = get_member_multiplier(member)
    final_text = int(text_points * multiplier)
    final_voice = int(voice_points * multiplier)

    if final_text > 0:
        remaining_text = max(0, DAILY_TEXT_CAP - daily_text)
        final_text = min(final_text, remaining_text)

    if final_voice > 0:
        remaining_voice = max(0, DAILY_VOICE_CAP - daily_voice)
        final_voice = min(final_voice, remaining_voice)

    if final_text > 0 or final_voice > 0:
        add_points_db(member.guild.id, member.id, text_points=final_text, voice_points=final_voice)

    return final_text, final_voice


async def apply_level_rewards(member: discord.Member) -> None:
    if member.bot:
        return

    row = get_points_row(member.guild.id, member.id)
    if row is None:
        return

    current_level = calculate_level(row["total_points"])
    rewards_to_have = {role_id for level, role_id in LEVEL_ROLE_REWARDS.items() if current_level >= level}

    if not rewards_to_have:
        return

    roles_to_add = []
    me = member.guild.me
    if me is None or not me.guild_permissions.manage_roles:
        return

    for role_id in rewards_to_have:
        role = member.guild.get_role(role_id)
        if role and role not in member.roles and role < me.top_role:
            roles_to_add.append(role)

    if roles_to_add:
        try:
            await member.add_roles(*roles_to_add, reason="Automatyczna nagroda poziomu XP")
        except discord.HTTPException as exc:
            logger.warning("Nie udało się dodać nagród poziomu dla %s: %s", member.id, exc)


def points_embed_for_user(member: discord.Member, row: sqlite3.Row) -> discord.Embed:
    level = calculate_level(row["total_points"])
    next_need = points_to_next_level(row["total_points"])

    embed = discord.Embed(title="🏆 Twoje punkty", color=discord.Color.blurple())
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)
    embed.add_field(name="📈 Poziom", value=str(level), inline=True)
    embed.add_field(name="⏭️ Do następnego poziomu", value=f"{next_need} pkt", inline=True)
    embed.set_footer(text=f"Użytkownik: {member.display_name}")
    return embed


def ranking_embed(guild: discord.Guild) -> discord.Embed:
    rows = get_top_users(guild.id, 10)
    embed = discord.Embed(title="🏆 Ranking serwera", color=discord.Color.gold())

    if not rows:
        embed.description = "Na tym serwerze nikt nie ma jeszcze punktów."
        return embed

    lines = []
    for index, row in enumerate(rows, start=1):
        member = guild.get_member(row["user_id"])
        name = member.display_name if member else f"Użytkownik {row['user_id']}"
        prefix = get_rank_prefix(member)
        level = calculate_level(row["total_points"])
        lines.append(
            f"**{index}.** {prefix}{name} — **{row['total_points']} pkt** | "
            f"Lvl **{level}** (💬 {row['text_points']} | 🎤 {row['voice_points']} | 📝 {row['message_count']})"
        )

    embed.description = "\n".join(lines)
    return embed


def xpinfo_embed() -> discord.Embed:
    embed = discord.Embed(title="📘 Zasady punktów", color=discord.Color.orange())
    embed.add_field(name="💬 Wiadomości", value=f"{TEXT_POINTS} punkty za każde {TEXT_MESSAGES_REQUIRED} sensownych wiadomości", inline=False)
    embed.add_field(name="🎤 VC", value=f"{VC_POINTS_SOLO} punktów za {VC_INTERVAL_SECONDS // 60} minut solo\n{VC_POINTS_WITH_ACTIVE} punktów za {VC_INTERVAL_SECONDS // 60} minut z aktywną osobą", inline=False)
    embed.add_field(name="⭐ Bonusy rang", value="VIP: +20%\nLEGENDA: +40%", inline=False)
    embed.add_field(name="❌ Punkty VC nie lecą gdy", value="bot / mute / deaf / kanał AFK", inline=False)
    embed.add_field(name="🛡️ Anty-spam", value="Krótki cooldown wiadomości i blokada identycznych powtórek", inline=False)
    embed.add_field(name="📈 Poziomy", value=f"1 poziom co {LEVEL_STEP} punktów", inline=False)
    return embed


def shop_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Sklep punktów",
        description="Kupuj role za punkty aktywności.",
        color=discord.Color.gold()
    )
    embed.add_field(name="⭐ VIP", value="Cena: **50 000 pkt**", inline=False)
    embed.add_field(name="💎 LEGENDA", value="Cena: **100 000 pkt**", inline=False)
    embed.set_footer(text="Możesz kupować przyciskami albo komendą /kup")
    return embed


def points_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="📊 Punkty",
        description="Kliknij przycisk poniżej albo użyj `/punkty` w tym kanale.",
        color=discord.Color.blue()
    )


def ranking_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="🏆 Ranking",
        description="Kliknij przycisk poniżej albo użyj `/ranking` w tym kanale.",
        color=discord.Color.gold()
    )


def xpinfo_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="📘 Info XP",
        description="Kliknij przycisk poniżej albo użyj `/xpinfo` w tym kanale.",
        color=discord.Color.orange()
    )


async def safe_interaction_send(
    interaction: discord.Interaction,
    *,
    content: Optional[str] = None,
    embed: Optional[discord.Embed] = None,
    view: Optional[discord.ui.View] = None,
    ephemeral: bool = False,
) -> None:
    try:
        if interaction.response.is_done():
            await interaction.followup.send(content=content, embed=embed, view=view, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content=content, embed=embed, view=view, ephemeral=ephemeral)
    except discord.HTTPException as exc:
        logger.warning("Nie udało się wysłać odpowiedzi interakcji: %s", exc)


async def ensure_panel_message(
    guild: discord.Guild,
    panel_key: str,
    embed: discord.Embed,
    view: Optional[discord.ui.View] = None
) -> None:
    channel_id = PANEL_CHANNELS[panel_key]
    channel = guild.get_channel(channel_id)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return

    saved = get_panel_message(guild.id, panel_key)
    message = None

    if saved:
        try:
            message = await channel.fetch_message(saved["message_id"])
        except (discord.NotFound, discord.HTTPException):
            message = None

    if message is None:
        message = await channel.send(embed=embed, view=view)
        save_panel_message(guild.id, panel_key, channel.id, message.id)
    else:
        await message.edit(embed=embed, view=view)

    try:
        if not message.pinned:
            await message.pin(reason="Panel bota XP")
    except discord.HTTPException:
        pass


async def refresh_all_panels(guild: discord.Guild) -> None:
    await ensure_panel_message(guild, "points", points_panel_embed(), UtilityView(bot))
    await ensure_panel_message(guild, "ranking", ranking_panel_embed(), UtilityView(bot))
    await ensure_panel_message(guild, "xpinfo", xpinfo_panel_embed(), UtilityView(bot))
    await ensure_panel_message(guild, "shop", shop_embed(), ShopView(bot))


async def process_shop_purchase(interaction: discord.Interaction, item_name: str) -> None:
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Kupowanie działa tylko w kanale 🛒・sklep.", ephemeral=True)
        return

    item_key = item_name.lower().strip()
    item = SHOP_ITEMS.get(item_key)
    if item is None:
        await safe_interaction_send(interaction, content="❌ Nie ma takiego przedmiotu.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    role = interaction.guild.get_role(item["role_id"])
    if member is None or role is None:
        await safe_interaction_send(interaction, content="❌ Nie udało się znaleźć użytkownika lub roli.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, member.id)
    if row is None:
        await safe_interaction_send(interaction, content="❌ Nie masz jeszcze punktów.", ephemeral=True)
        return

    if row["total_points"] < item["price"]:
        await safe_interaction_send(interaction, content=f"❌ Za mało punktów. Potrzebujesz **{item['price']} pkt**.", ephemeral=True)
        return

    if role in member.roles:
        await safe_interaction_send(interaction, content="❌ Masz już tę rolę.", ephemeral=True)
        return

    try:
        if role.id == LEGEND_ROLE_ID:
            vip_role = interaction.guild.get_role(VIP_ROLE_ID)
            if vip_role and vip_role in member.roles:
                await member.remove_roles(vip_role, reason="Awans na LEGENDĘ")

        await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")
        ok = remove_total_points(interaction.guild.id, member.id, item["price"])
        if not ok:
            await safe_interaction_send(interaction, content="❌ Nie udało się odjąć punktów.", ephemeral=True)
            return

        embed = discord.Embed(
            title="✅ Zakup udany",
            description=f"Kupiłeś **{item['label']}** za **{item['price']} pkt**.",
            color=discord.Color.green()
        )

        if role.id == LEGEND_ROLE_ID:
            embed.add_field(name="💎 Bonus Legendy", value="Masz teraz +40% punktów i dostęp do kanałów legendy.", inline=False)
        elif role.id == VIP_ROLE_ID:
            embed.add_field(name="⭐ Bonus VIP", value="Masz teraz +20% punktów.", inline=False)

        await safe_interaction_send(interaction, embed=embed, ephemeral=True)
    except discord.Forbidden:
        await safe_interaction_send(interaction, content="❌ Bot nie może nadać tej roli. Ustaw rolę bota wyżej niż VIP i LEGENDA.", ephemeral=True)
    except Exception as exc:
        await safe_interaction_send(interaction, content=f"❌ Błąd przy zakupie: {exc}", ephemeral=True)


# =========================================================
# GUI
# =========================================================
class UtilityView(discord.ui.View):
    def __init__(self, bot_instance: XPBot):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="📊 Pokaż punkty", style=discord.ButtonStyle.primary, custom_id="xp_points_button")
    async def points_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        row = get_points_row(interaction.guild.id, interaction.user.id)
        member = interaction.guild.get_member(interaction.user.id)
        if row is None or member is None:
            await safe_interaction_send(interaction, content="Nie masz jeszcze punktów.", ephemeral=True)
            return

        await safe_interaction_send(interaction, embed=points_embed_for_user(member, row), ephemeral=True)

    @discord.ui.button(label="🏆 Pokaż ranking", style=discord.ButtonStyle.success, custom_id="xp_ranking_button")
    async def ranking_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        await safe_interaction_send(interaction, embed=ranking_embed(interaction.guild), ephemeral=True)

    @discord.ui.button(label="📘 Zasady XP", style=discord.ButtonStyle.secondary, custom_id="xp_info_button")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await safe_interaction_send(interaction, embed=xpinfo_embed(), ephemeral=True)


class ShopView(discord.ui.View):
    def __init__(self, bot_instance: XPBot):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="VIP", emoji="⭐", style=discord.ButtonStyle.success, custom_id="shop_vip")
    async def buy_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "vip")

    @discord.ui.button(label="LEGENDA", emoji="💎", style=discord.ButtonStyle.danger, custom_id="shop_legenda")
    async def buy_legenda(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "legenda")


# =========================================================
# EVENTY
# =========================================================
@bot.event
async def on_message(message: discord.Message):
    if not can_count_message(message):
        await bot.process_commands(message)
        return

    count = update_message_count(message.guild.id, message.author.id)

    if count % TEXT_MESSAGES_REQUIRED == 0:
        member = message.guild.get_member(message.author.id)
        if member:
            added_text, _ = add_points_with_role_bonus(member, text_points=TEXT_POINTS)
            if added_text > 0:
                await apply_level_rewards(member)

    await bot.process_commands(message)


@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    key = (member.guild.id, member.id)
    if is_active_for_vc(member):
        if key not in bot.vc_active_since:
            bot.vc_active_since[key] = time.time()
    else:
        bot.vc_active_since.pop(key, None)


@bot.event
async def on_raw_message_delete(payload: discord.RawMessageDeleteEvent):
    guild = bot.get_guild(payload.guild_id) if payload.guild_id else None
    if guild is None:
        return

    for row in get_all_panel_messages(guild.id):
        if row["message_id"] == payload.message_id:
            try:
                await refresh_all_panels(guild)
                logger.info("Odtworzono panel %s po usunięciu wiadomości.", row["panel_key"])
            except Exception as exc:
                logger.warning("Nie udało się odtworzyć panelu po usunięciu: %s", exc)
            break


@bot.event
async def on_ready():
    logger.info("Zalogowano jako %s", bot.user)

    for guild in bot.guilds:
        for member in guild.members:
            if is_active_for_vc(member):
                bot.vc_active_since[(guild.id, member.id)] = time.time()
        await refresh_all_panels(guild)

    if not vc_loop.is_running():
        vc_loop.start()

    try:
        synced = await bot.tree.sync()
        logger.info("Zsynchronizowano %s komend slash.", len(synced))
    except Exception as exc:
        logger.error("Błąd synchronizacji komend: %s", exc)


# =========================================================
# VC LOOP
# =========================================================
@tasks.loop(seconds=60)
async def vc_loop():
    now = time.time()

    for (guild_id, user_id), started_at in list(bot.vc_active_since.items()):
        guild = bot.get_guild(guild_id)
        if guild is None:
            bot.vc_active_since.pop((guild_id, user_id), None)
            continue

        member = guild.get_member(user_id)
        if member is None or not is_active_for_vc(member):
            bot.vc_active_since.pop((guild_id, user_id), None)
            continue

        elapsed = now - started_at
        if elapsed < VC_INTERVAL_SECONDS:
            continue

        full_intervals = int(elapsed // VC_INTERVAL_SECONDS)
        channel = member.voice.channel
        active_count = count_active_members_in_channel(channel)
        base_points = VC_POINTS_WITH_ACTIVE if active_count >= 2 else VC_POINTS_SOLO

        _, added_voice = add_points_with_role_bonus(member, voice_points=full_intervals * base_points)
        if added_voice > 0:
            await apply_level_rewards(member)

        bot.vc_active_since[(guild_id, user_id)] = started_at + (full_intervals * VC_INTERVAL_SECONDS)


@vc_loop.before_loop
async def before_vc_loop():
    await bot.wait_until_ready()


# =========================================================
# KOMENDY SLASH
# =========================================================
@bot.tree.command(name="punkty", description="Pokazuje Twoje punkty")
async def punkty(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != POINTS_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 📊・sprawdz-punkty.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, interaction.user.id)
    member = interaction.guild.get_member(interaction.user.id)
    if row is None or member is None:
        await safe_interaction_send(interaction, content="Nie masz jeszcze żadnych punktów.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=points_embed_for_user(member, row), ephemeral=True)


@bot.tree.command(name="punkty_uzytkownika", description="Pokazuje punkty wybranego użytkownika")
@app_commands.describe(uzytkownik="Wybierz użytkownika")
async def punkty_uzytkownika(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != POINTS_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 📊・sprawdz-punkty.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, uzytkownik.id)
    if row is None:
        await safe_interaction_send(interaction, content="Ten użytkownik nie ma jeszcze punktów.", ephemeral=True)
        return

    embed = discord.Embed(title=f"🏆 Punkty użytkownika: {uzytkownik.display_name}", color=discord.Color.green())
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)
    embed.add_field(name="📈 Poziom", value=str(calculate_level(row["total_points"])), inline=False)

    await safe_interaction_send(interaction, embed=embed, ephemeral=True)


@bot.tree.command(name="ranking", description="Pokazuje ranking serwera")
async def ranking(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != RANKING_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 🏆・ranking.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=ranking_embed(interaction.guild), ephemeral=False)


@bot.tree.command(name="xpinfo", description="Pokazuje zasady punktów")
async def xpinfo(interaction: discord.Interaction):
    if interaction.channel_id != XPINFO_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 📘・info-xp.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=xpinfo_embed(), ephemeral=False)


@bot.tree.command(name="sklep", description="Pokazuje sklep punktów")
async def sklep(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 🛒・sklep.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=shop_embed(), view=ShopView(bot), ephemeral=False)


@bot.tree.command(name="kup", description="Kup przedmiot ze sklepu")
@app_commands.describe(przedmiot="vip albo legenda")
async def kup(interaction: discord.Interaction, przedmiot: str):
    await process_shop_purchase(interaction, przedmiot)


@bot.tree.command(name="odswiez_panele", description="Odświeża wszystkie panele bota")
@app_commands.checks.has_permissions(manage_guild=True)
async def odswiez_panele(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await refresh_all_panels(interaction.guild)
    await safe_interaction_send(interaction, content="✅ Panele zostały odświeżone.", ephemeral=True)


@bot.tree.command(name="dodaj_punkty", description="Dodaje punkty użytkownikowi")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(uzytkownik="Wybierz użytkownika", ilosc="Liczba punktów")
async def dodaj_punkty(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    if ilosc <= 0:
        await safe_interaction_send(interaction, content="❌ Ilość musi być większa od zera.", ephemeral=True)
        return

    add_total_points(interaction.guild.id, uzytkownik.id, ilosc)
    await safe_interaction_send(interaction, content=f"✅ Dodano **{ilosc} pkt** użytkownikowi **{uzytkownik.display_name}**.", ephemeral=True)


@bot.tree.command(name="zabierz_punkty", description="Zabiera punkty użytkownikowi")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(uzytkownik="Wybierz użytkownika", ilosc="Liczba punktów")
async def zabierz_punkty(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    if ilosc <= 0:
        await safe_interaction_send(interaction, content="❌ Ilość musi być większa od zera.", ephemeral=True)
        return

    ok = remove_total_points(interaction.guild.id, uzytkownik.id, ilosc)
    if not ok:
        await safe_interaction_send(interaction, content="❌ Użytkownik ma za mało punktów.", ephemeral=True)
        return

    await safe_interaction_send(interaction, content=f"✅ Zabrano **{ilosc} pkt** użytkownikowi **{uzytkownik.display_name}**.", ephemeral=True)


@bot.tree.command(name="ustaw_punkty", description="Ustawia dokładną liczbę punktów użytkownikowi")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(uzytkownik="Wybierz użytkownika", ilosc="Nowa liczba punktów")
async def ustaw_punkty(interaction: discord.Interaction, uzytkownik: discord.Member, ilosc: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    if ilosc < 0:
        await safe_interaction_send(interaction, content="❌ Liczba punktów nie może być ujemna.", ephemeral=True)
        return

    set_total_points(interaction.guild.id, uzytkownik.id, ilosc)
    await safe_interaction_send(interaction, content=f"✅ Ustawiono **{ilosc} pkt** użytkownikowi **{uzytkownik.display_name}**.", ephemeral=True)


@bot.tree.command(name="level", description="Pokazuje Twój poziom")
async def level(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, interaction.user.id)
    if row is None:
        await safe_interaction_send(interaction, content="Nie masz jeszcze punktów.", ephemeral=True)
        return

    lvl = calculate_level(row["total_points"])
    nxt = points_to_next_level(row["total_points"])
    await safe_interaction_send(interaction, content=f"📈 Masz poziom **{lvl}**. Do następnego poziomu brakuje **{nxt} pkt**.", ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    logger.error("Błąd komendy slash: %s", error)

    if isinstance(error, app_commands.MissingPermissions):
        msg = "❌ Nie masz uprawnień do tej komendy."
    else:
        msg = f"❌ Błąd komendy: {error}"

    await safe_interaction_send(interaction, content=msg, ephemeral=True)


# =========================================================
# START
# =========================================================
def main() -> None:
    if not TOKEN:
        raise RuntimeError("Brak zmiennej TOKEN lub DISCORD_TOKEN.")
    init_db()
    logger.info("Start bota XP. Baza: %s | Log: %s", DB_FILE, LOG_FILE)
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
