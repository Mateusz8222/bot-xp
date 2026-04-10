import os
import random
import time
from datetime import datetime, timezone
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

# =========================================================
# KONFIG
# =========================================================
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# =========================================================
# ID KANAŁÓW
# =========================================================
POINTS_CHANNEL_ID = 1490629053286191206      # 📊・sprawdz-punkty
RANKING_CHANNEL_ID = 1490629324305600594     # 🏆・ranking
XPINFO_CHANNEL_ID = 1490629632796524554      # 📘・info-xp
SHOP_CHANNEL_ID = 1490648124006338640        # 🛒・sklep

LEGEND_TEXT_CHANNEL_ID = 1490791025671803013 # 💎・legenda-czat
LEGEND_VC_CHANNEL_ID = 1490792255504646407   # 💎・Legenda VC
SHOP_LOG_CHANNEL_ID = 1491934996745683035      # 📜・logi-pod-sklep
ADMIN_LOG_CHANNEL_ID = 1491944667124596836     # 📜・logi-administracyjne

# =========================================================
# AUTO PRYWATNE KANAŁY VC
# =========================================================
PRIVATE_CHANNEL_CATEGORY_NAME = "🔒 Prywatne kanały"
PRIVATE_CHANNEL_PREFIX = "🔒・"

# =========================================================
# ID RÓL
# =========================================================
VIP_ROLE_ID = 1474567627895738388
LEGEND_ROLE_ID = 1490683484262498335
PRIVATE_CHANNEL_ROLE_ID = 1475970739986239620  # 🔑 moderator kanału prywatnego
SIGMA_ROLE_ID = 1491572107539120128            # 😎 SIGMA

GOLD_MEDAL_ROLE_ID = 1491590645599441109
SILVER_MEDAL_ROLE_ID = 1491589877291024486
BRONZE_MEDAL_ROLE_ID = 1491588730249679108
AURA_ROLE_ID = 1491917610281861231  # 🌌 AURA

# =========================================================
# USTAWIENIA XP
# =========================================================
TEXT_MESSAGES_REQUIRED = 10
TEXT_POINTS = 2

VC_INTERVAL_SECONDS = 30  # 30 sekund
VC_POINTS_SOLO = 1

VIP_MULTIPLIER = 1.20
LEGEND_MULTIPLIER = 1.40

# =========================================================
# SKRZYNKI
# =========================================================
CRATE_COOLDOWN_SECONDS = 30

CRATE_CONFIG = {
    "crate_basic": {
        "price": 10000,
        "label": "📦 Zwykła skrzynka",
        "emoji": "📦",
        "description": "Podstawowa skrzynka z punktami, szansą na medal i pustym dropem.",
        "rewards": [
            {"type": "role", "value": BRONZE_MEDAL_ROLE_ID, "weight": 10, "name": "🥉 Brązowy Medal"},
            {"type": "nothing", "value": None, "weight": 15, "name": "❌ Pusta skrzynka"},
            {"type": "points", "value": 5000, "weight": 20, "name": "5 000 pkt"},
            {"type": "points", "value": 8000, "weight": 20, "name": "8 000 pkt"},
            {"type": "points", "value": 12000, "weight": 20, "name": "12 000 pkt"},
            {"type": "points", "value": 15000, "weight": 15, "name": "15 000 pkt"},
        ],
    },
    "crate_mystery": {
        "price": 20000,
        "label": "🎰 Mystery Box",
        "emoji": "🎰",
        "description": "Ryzykowna skrzynka z punktami, medalem, SIGMĄ albo pustką.",
        "rewards": [
            {"type": "nothing", "value": None, "weight": 18, "name": "❌ Pusta skrzynka"},
            {"type": "points", "value": 5000, "weight": 20, "name": "5 000 pkt"},
            {"type": "points", "value": 10000, "weight": 20, "name": "10 000 pkt"},
            {"type": "points", "value": 20000, "weight": 18, "name": "20 000 pkt"},
            {"type": "points", "value": 35000, "weight": 12, "name": "35 000 pkt"},
            {"type": "role", "value": BRONZE_MEDAL_ROLE_ID, "weight": 8, "name": "🥉 Brązowy Medal"},
            {"type": "role", "value": SIGMA_ROLE_ID, "weight": 4, "name": "😎 SIGMA"},
        ],
    },
    "crate_premium": {
        "price": 25000,
        "label": "🎁 Premium skrzynka",
        "emoji": "🎁",
        "description": "Lepsze punkty, medale i szansa na rangę SIGMA.",
        "rewards": [
            {"type": "role", "value": BRONZE_MEDAL_ROLE_ID, "weight": 15, "name": "🥉 Brązowy Medal"},
            {"type": "role", "value": SILVER_MEDAL_ROLE_ID, "weight": 8, "name": "🥈 Srebrny Medal"},
            {"type": "role", "value": SIGMA_ROLE_ID, "weight": 5, "name": "😎 SIGMA"},
            {"type": "nothing", "value": None, "weight": 12, "name": "❌ Pusta skrzynka"},
            {"type": "points", "value": 15000, "weight": 20, "name": "15 000 pkt"},
            {"type": "points", "value": 20000, "weight": 15, "name": "20 000 pkt"},
            {"type": "points", "value": 30000, "weight": 15, "name": "30 000 pkt"},
            {"type": "points", "value": 40000, "weight": 10, "name": "40 000 pkt"},
        ],
    },
    "crate_legendary": {
        "price": 60000,
        "label": "💎 Legendarna skrzynka",
        "emoji": "💎",
        "description": "Najmocniejsza skrzynka z top nagrodami i legendarnymi dropami.",
        "rewards": [
            {"type": "role", "value": BRONZE_MEDAL_ROLE_ID, "weight": 15, "name": "🥉 Brązowy Medal"},
            {"type": "role", "value": SILVER_MEDAL_ROLE_ID, "weight": 10, "name": "🥈 Srebrny Medal"},
            {"type": "role", "value": GOLD_MEDAL_ROLE_ID, "weight": 5, "name": "🥇 Złoty Medal"},
            {"type": "role", "value": VIP_ROLE_ID, "weight": 10, "name": "⭐ VIP"},
            {"type": "role", "value": SIGMA_ROLE_ID, "weight": 10, "name": "😎 SIGMA"},
            {"type": "role", "value": LEGEND_ROLE_ID, "weight": 3, "name": "💎 LEGENDA"},
            {"type": "nothing", "value": None, "weight": 7, "name": "❌ Pusta skrzynka"},
            {"type": "points", "value": 30000, "weight": 15, "name": "30 000 pkt"},
            {"type": "points", "value": 50000, "weight": 10, "name": "50 000 pkt"},
            {"type": "points", "value": 70000, "weight": 8, "name": "70 000 pkt"},
            {"type": "points", "value": 100000, "weight": 7, "name": "100 000 pkt"},
        ],
    },
}

# =========================================================
# SKLEP
# =========================================================
SHOP_ITEMS = {
    "crate_basic": {"price": 10000, "label": "📦 Zwykła skrzynka"},
    "crate_mystery": {"price": 20000, "label": "🎰 Mystery Box"},
    "xp_booster": {"price": 20000, "label": "⚡ Booster XP 1h"},
    "crate_premium": {"price": 25000, "label": "🎁 Premium skrzynka"},
    "auto_prywatny_kanal": {
        "price": 30000,
        "role_id": PRIVATE_CHANNEL_ROLE_ID,
        "label": "🛠️ Auto prywatny kanał",
    },
    "sigma": {
        "price": 40000,
        "role_id": SIGMA_ROLE_ID,
        "label": "😎 SIGMA",
    },
    "aura": {
        "price": 45000,
        "role_id": AURA_ROLE_ID,
        "label": "🌌 AURA",
    },
    "vip": {
        "price": 50000,
        "role_id": VIP_ROLE_ID,
        "label": "⭐ VIP",
    },
    "crate_legendary": {"price": 60000, "label": "💎 Legendarna skrzynka"},
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
# BAZA DANYCH
# =========================================================
USING_POSTGRES = bool(DATABASE_URL)

if USING_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3
    from pathlib import Path

    DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SQLITE_DB_FILE = str(DATA_DIR / "xp.db")

def db_connect():
    if USING_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        conn.autocommit = False
        return conn

    conn = sqlite3.connect(SQLITE_DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn

def sql(query: str) -> str:
    if USING_POSTGRES:
        return query.replace("?", "%s")
    return query

def fetchone_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)

def init_db() -> None:
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS points (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                text_points INTEGER NOT NULL DEFAULT 0,
                voice_points INTEGER NOT NULL DEFAULT 0,
                total_points INTEGER NOT NULL DEFAULT 0,
                message_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS panel_messages (
                guild_id BIGINT NOT NULL,
                panel_key TEXT NOT NULL,
                channel_id BIGINT NOT NULL,
                message_id BIGINT NOT NULL,
                PRIMARY KEY (guild_id, panel_key)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crate_cooldowns (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                crate_key TEXT NOT NULL,
                next_open_at BIGINT NOT NULL,
                PRIMARY KEY (guild_id, user_id, crate_key)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS xp_boosts (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                multiplier REAL NOT NULL,
                expires_at BIGINT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS xp_boosts (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                multiplier REAL NOT NULL,
                expires_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crate_history (
                id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                crate_key TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT,
                created_at BIGINT NOT NULL
            )
        """)
    else:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS points (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                text_points INTEGER NOT NULL DEFAULT 0,
                voice_points INTEGER NOT NULL DEFAULT 0,
                total_points INTEGER NOT NULL DEFAULT 0,
                message_count INTEGER NOT NULL DEFAULT 0,
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
            CREATE TABLE IF NOT EXISTS crate_cooldowns (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                crate_key TEXT NOT NULL,
                next_open_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id, crate_key)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS crate_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                crate_key TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT,
                created_at INTEGER NOT NULL
            )
        """)

    conn.commit()
    conn.close()

def ensure_user_row(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO points (
                guild_id, user_id, text_points, voice_points, total_points, message_count
            ) VALUES (%s, %s, 0, 0, 0, 0)
            ON CONFLICT (guild_id, user_id) DO NOTHING
        """, (guild_id, user_id))
    else:
        cur.execute("""
            INSERT OR IGNORE INTO points (
                guild_id, user_id, text_points, voice_points, total_points, message_count
            ) VALUES (?, ?, 0, 0, 0, 0)
        """, (guild_id, user_id))

    conn.commit()
    conn.close()

def get_points_row(guild_id: int, user_id: int) -> Optional[dict]:
    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT text_points, voice_points, total_points, message_count
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)
    conn.close()
    return row

def update_message_count(guild_id: int, user_id: int) -> int:
    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE points
        SET message_count = message_count + 1
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    cur.execute(sql("""
        SELECT message_count
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    count_row = fetchone_dict(cur)
    conn.commit()
    conn.close()
    return int(count_row["message_count"]) if count_row else 0

def add_points_db(guild_id: int, user_id: int, *, text_points: int = 0, voice_points: int = 0) -> None:
    ensure_user_row(guild_id, user_id)
    total_add = int(text_points) + int(voice_points)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE points
        SET text_points = text_points + ?,
            voice_points = voice_points + ?,
            total_points = total_points + ?
        WHERE guild_id = ? AND user_id = ?
    """), (int(text_points), int(voice_points), total_add, guild_id, user_id))
    conn.commit()
    conn.close()

def add_points(guild_id: int, user_id: int, amount: int) -> None:
    add_points_db(guild_id, user_id, text_points=int(amount), voice_points=0)

def remove_total_points(guild_id: int, user_id: int, amount: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE points
        SET total_points = CASE
            WHEN total_points - ? < 0 THEN 0
            ELSE total_points - ?
        END
        WHERE guild_id = ? AND user_id = ?
    """), (int(amount), int(amount), guild_id, user_id))
    conn.commit()
    conn.close()

def reset_user_points(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE points
        SET text_points = 0,
            voice_points = 0,
            total_points = 0,
            message_count = 0
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    conn.commit()
    conn.close()

def delete_user_data(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(sql("""
        DELETE FROM points
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))

    cur.execute(sql("""
        DELETE FROM xp_boosts
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))

    cur.execute(sql("""
        DELETE FROM crate_cooldowns
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))

    cur.execute(sql("""
        DELETE FROM crate_history
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))

    conn.commit()
    conn.close()

def get_top_users(guild_id: int, limit: int = 10) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT user_id, text_points, voice_points, total_points, message_count
        FROM points
        WHERE guild_id = ?
        ORDER BY total_points DESC, voice_points DESC, text_points DESC
        LIMIT ?
    """), (guild_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_panel_message(guild_id: int, panel_key: str, channel_id: int, message_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO panel_messages (guild_id, panel_key, channel_id, message_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (guild_id, panel_key)
            DO UPDATE SET channel_id = EXCLUDED.channel_id, message_id = EXCLUDED.message_id
        """, (guild_id, panel_key, channel_id, message_id))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO panel_messages (guild_id, panel_key, channel_id, message_id)
            VALUES (?, ?, ?, ?)
        """, (guild_id, panel_key, channel_id, message_id))

    conn.commit()
    conn.close()

def get_panel_message(guild_id: int, panel_key: str) -> Optional[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT channel_id, message_id
        FROM panel_messages
        WHERE guild_id = ? AND panel_key = ?
    """), (guild_id, panel_key))
    row = fetchone_dict(cur)
    conn.close()
    return row

def get_crate_cooldown(guild_id: int, user_id: int, crate_key: str) -> int:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT next_open_at
        FROM crate_cooldowns
        WHERE guild_id = ? AND user_id = ? AND crate_key = ?
    """), (guild_id, user_id, crate_key))
    row = fetchone_dict(cur)
    conn.close()
    return int(row["next_open_at"]) if row else 0

def set_crate_cooldown(guild_id: int, user_id: int, crate_key: str, next_open_at: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO crate_cooldowns (guild_id, user_id, crate_key, next_open_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (guild_id, user_id, crate_key)
            DO UPDATE SET next_open_at = EXCLUDED.next_open_at
        """, (guild_id, user_id, crate_key, int(next_open_at)))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO crate_cooldowns (guild_id, user_id, crate_key, next_open_at)
            VALUES (?, ?, ?, ?)
        """, (guild_id, user_id, crate_key, int(next_open_at)))
    conn.commit()
    conn.close()

def add_crate_history(guild_id: int, user_id: int, crate_key: str, reward_type: str, reward_value: Optional[str]) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        INSERT INTO crate_history (guild_id, user_id, crate_key, reward_type, reward_value, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """), (guild_id, user_id, crate_key, reward_type, reward_value, int(time.time())))
    conn.commit()
    conn.close()

def get_last_crate_history(guild_id: int, user_id: int, limit: int = 5) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT crate_key, reward_type, reward_value, created_at
        FROM crate_history
        WHERE guild_id = ? AND user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """), (guild_id, user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_active_xp_boost(guild_id: int, user_id: int) -> float:
    now_ts = int(time.time())
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT multiplier, expires_at
        FROM xp_boosts
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)
    conn.close()
    if not row:
        return 1.0
    if int(row["expires_at"]) <= now_ts:
        clear_xp_boost(guild_id, user_id)
        return 1.0
    return float(row["multiplier"])

def set_xp_boost(guild_id: int, user_id: int, multiplier: float, expires_at: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO xp_boosts (guild_id, user_id, multiplier, expires_at)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET multiplier = EXCLUDED.multiplier, expires_at = EXCLUDED.expires_at
        """, (guild_id, user_id, multiplier, int(expires_at)))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO xp_boosts (guild_id, user_id, multiplier, expires_at)
            VALUES (?, ?, ?, ?)
        """, (guild_id, user_id, multiplier, int(expires_at)))
    conn.commit()
    conn.close()

def clear_xp_boost(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        DELETE FROM xp_boosts
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    conn.commit()
    conn.close()

def get_total_multiplier(member: discord.Member) -> float:
    return get_member_multiplier(member) * get_active_xp_boost(member.guild.id, member.id)

async def send_shop_log(guild: discord.Guild, embed: discord.Embed) -> None:
    channel = guild.get_channel(SHOP_LOG_CHANNEL_ID)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(embed=embed)
    except Exception:
        pass

async def send_admin_log(guild: discord.Guild, embed: discord.Embed) -> None:
    channel = guild.get_channel(ADMIN_LOG_CHANNEL_ID)
    if channel is None or not isinstance(channel, discord.TextChannel):
        return
    try:
        await channel.send(embed=embed)
    except Exception:
        pass

async def get_recent_audit_actor_and_reason(
    guild: discord.Guild,
    action: discord.AuditLogAction,
    target_id: int,
    *,
    seconds_back: int = 20,
):
    try:
        async for entry in guild.audit_logs(limit=6, action=action):
            if entry.target and getattr(entry.target, "id", None) == target_id:
                created = entry.created_at
                if created is not None:
                    age = (datetime.now(timezone.utc) - created).total_seconds()
                    if age <= seconds_back:
                        return entry.user, entry.reason
    except Exception:
        return None, None
    return None, None

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

    async def setup_hook(self) -> None:
        self.add_view(ShopView(self))
        self.add_view(PointsView(self))
        self.add_view(RankingView(self))
        self.add_view(XpInfoView(self))

bot = XPBot()

# =========================================================
# POMOCNICZE
# =========================================================
async def safe_interaction_send(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    ephemeral: bool = False,
) -> None:
    kwargs = {"ephemeral": ephemeral}

    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view

    try:
        if interaction.response.is_done():
            await interaction.followup.send(**kwargs)
        else:
            await interaction.response.send_message(**kwargs)
    except discord.InteractionResponded:
        await interaction.followup.send(**kwargs)

def get_member_multiplier(member: discord.Member) -> float:
    role_ids = {role.id for role in member.roles}
    if LEGEND_ROLE_ID in role_ids:
        return LEGEND_MULTIPLIER
    if VIP_ROLE_ID in role_ids:
        return VIP_MULTIPLIER
    return 1.0

def add_points_with_role_bonus(member: discord.Member, *, text_points: int = 0, voice_points: int = 0) -> None:
    multiplier = get_total_multiplier(member)
    final_text = int(text_points * multiplier)
    final_voice = int(voice_points * multiplier)
    add_points_db(member.guild.id, member.id, text_points=final_text, voice_points=final_voice)

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

def get_rank_prefix(member: Optional[discord.Member]) -> str:
    if member is None:
        return ""
    role_ids = {role.id for role in member.roles}
    if LEGEND_ROLE_ID in role_ids:
        return "💎 "
    if VIP_ROLE_ID in role_ids:
        return "⭐ "
    if SIGMA_ROLE_ID in role_ids:
        return "😎 "
    return ""

def get_reward_role_name(role_id: int) -> str:
    mapping = {
        BRONZE_MEDAL_ROLE_ID: "🥉 Brązowy Medal",
        SILVER_MEDAL_ROLE_ID: "🥈 Srebrny Medal",
        GOLD_MEDAL_ROLE_ID: "🥇 Złoty Medal",
        SIGMA_ROLE_ID: "😎 SIGMA",
        VIP_ROLE_ID: "⭐ VIP",
        LEGEND_ROLE_ID: "💎 LEGENDA",
    }
    return mapping.get(role_id, f"Rola {role_id}")

def is_real_user(obj) -> bool:
    return not getattr(obj, "bot", False)

def sanitize_private_channel_name(name: str) -> str:
    safe = name.lower().strip()
    replacements = {
        "ą": "a", "ć": "c", "ę": "e", "ł": "l", "ń": "n",
        "ó": "o", "ś": "s", "ż": "z", "ź": "z",
    }
    for old, new in replacements.items():
        safe = safe.replace(old, new)

    allowed = []
    for ch in safe:
        if ch.isalnum() or ch in {"-", "_"}:
            allowed.append(ch)
        elif ch in {" ", "."}:
            allowed.append("-")

    safe = "".join(allowed)
    while "--" in safe:
        safe = safe.replace("--", "-")
    safe = safe.strip("-_")
    if not safe:
        safe = "uzytkownik"
    return f"{PRIVATE_CHANNEL_PREFIX}{safe[:80]}"

async def create_or_get_private_channel_for_member(guild: discord.Guild, member: discord.Member) -> discord.VoiceChannel:
    category = discord.utils.get(guild.categories, name=PRIVATE_CHANNEL_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(PRIVATE_CHANNEL_CATEGORY_NAME, reason="Auto prywatne kanały")

    expected_name = sanitize_private_channel_name(member.display_name)

    for channel in category.voice_channels:
        overwrites = channel.overwrites_for(member)
        if channel.name == expected_name or overwrites.view_channel is True:
            return channel

    bot_member = guild.me
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
            stream=True,
            use_voice_activation=True,
        ),
    }
    if bot_member is not None:
        overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
            manage_channels=True,
            move_members=True,
        )

    role = guild.get_role(PRIVATE_CHANNEL_ROLE_ID)
    if role is not None:
        overwrites[role] = discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=True,
        )

    channel = await guild.create_voice_channel(
        name=expected_name,
        category=category,
        overwrites=overwrites,
        reason=f"Auto prywatny kanał dla {member}",
    )
    return channel

def points_embed_for_user(member: discord.Member, row: dict) -> discord.Embed:
    embed = discord.Embed(title="🏆 Twoje punkty", color=discord.Color.blurple())
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)
    embed.set_footer(text=f"Użytkownik: {member.display_name}")
    return embed

def ranking_embed(guild: discord.Guild) -> discord.Embed:
    rows = get_top_users(guild.id, 50)
    embed = discord.Embed(title="🏆 Ranking serwera", color=discord.Color.gold())

    lines = []
    position = 1

    for row in rows:
        member = guild.get_member(int(row["user_id"]))
        if member is None or member.bot:
            continue

        prefix = get_rank_prefix(member)
        lines.append(
            f"**{position}.** {prefix}{member.display_name} — **{row['total_points']} pkt** "
            f"(💬 {row['text_points']} | 🎤 {row['voice_points']} | 📝 {row['message_count']})"
        )
        position += 1

        if position > 10:
            break

    if not lines:
        embed.description = "Na tym serwerze nikt nie ma jeszcze punktów."
        return embed

    embed.description = "\n".join(lines)
    return embed

def xpinfo_embed() -> discord.Embed:
    embed = discord.Embed(title="📘 Zasady punktów", color=discord.Color.orange())
    embed.add_field(name="💬 Wiadomości", value="2 punkty za każde 10 wiadomości", inline=False)
    embed.add_field(
        name="🎤 VC",
        value="1 punkt za 30 sekund solo\n2+ osoby: punkty co 30 sekund = liczba aktywnych osób na kanale",
        inline=False,
    )
    embed.add_field(name="⭐ Bonusy rang", value="VIP: +20%\nLEGENDA: +40%", inline=False)
    embed.add_field(name="📦 Skrzynki", value="Mogą wypaść punkty, role, medale albo pusta skrzynka.", inline=False)
    embed.add_field(name="⚡ Booster XP", value="+25% XP przez 1 godzinę po zakupie.", inline=False)
    embed.add_field(name="🌌 AURA", value="Prestiżowa rola wizualna do kupienia w sklepie.", inline=False)
    embed.add_field(name="❌ Punkty VC nie lecą gdy", value="bot / mute / deaf / kanał AFK", inline=False)
    return embed

def shop_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Sklep punktów",
        description="Kupuj role, funkcje i skrzynki za punkty aktywności.",
        color=discord.Color.gold(),
    )

    sorted_items = sorted(SHOP_ITEMS.values(), key=lambda item: item["price"])

    for item in sorted_items:
        embed.add_field(
            name=item["label"],
            value=f"Cena: **{item['price']:,} pkt**".replace(",", " "),
            inline=False,
        )

    embed.set_footer(text="Możesz kupować przyciskami albo komendą /kup")
    return embed

def points_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="📊 Punkty",
        description="Kliknij przycisk poniżej albo użyj `/punkty` w tym kanale.",
        color=discord.Color.blue(),
    )

def ranking_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="🏆 Ranking",
        description="Kliknij przycisk poniżej albo użyj `/ranking` w tym kanale.",
        color=discord.Color.gold(),
    )

def xpinfo_panel_embed() -> discord.Embed:
    return discord.Embed(
        title="📘 Info XP",
        description="Kliknij przycisk poniżej albo użyj `/xpinfo` w tym kanale.",
        color=discord.Color.orange(),
    )

def crate_result_embed(crate_key: str, reward_type: str, reward_value: Optional[str], member: discord.Member) -> discord.Embed:
    crate = CRATE_CONFIG[crate_key]
    color = discord.Color.random()

    if reward_type == "points":
        title = f"{crate['emoji']} Otworzyłeś {crate['label']}"
        desc = f"🎉 **{member.display_name}** wygrał **{reward_value} pkt**!"
        color = discord.Color.green()
    elif reward_type == "role":
        title = f"{crate['emoji']} Otworzyłeś {crate['label']}"
        desc = f"🏅 **{member.display_name}** zdobył **{reward_value}**!"
        color = discord.Color.gold()
    else:
        title = f"{crate['emoji']} Otworzyłeś {crate['label']}"
        desc = f"❌ **{member.display_name}** trafił pustą skrzynkę."
        color = discord.Color.red()

    embed = discord.Embed(title=title, description=desc, color=color)
    embed.set_footer(text="Powodzenia przy następnym otwarciu 😎")
    return embed

def crate_history_embed(member: discord.Member, history: list[dict]) -> discord.Embed:
    embed = discord.Embed(
        title="📜 Ostatnie skrzynki",
        description=f"Ostatnie otwarcia skrzynek użytkownika **{member.display_name}**",
        color=discord.Color.blurple(),
    )

    if not history:
        embed.description = "Brak historii skrzynek."
        return embed

    lines = []
    for item in history:
        crate_label = CRATE_CONFIG.get(item["crate_key"], {}).get("label", item["crate_key"])
        reward_type = item["reward_type"]
        reward_value = item["reward_value"] or "nic"
        ts = int(item["created_at"])
        if reward_type == "points":
            reward_text = f"{reward_value} pkt"
        elif reward_type == "role":
            reward_text = reward_value
        else:
            reward_text = "❌ pusta skrzynka"

        lines.append(f"• **{crate_label}** → {reward_text} <t:{ts}:R>")

    embed.description = "\n".join(lines)
    return embed

def choose_crate_reward(crate_key: str) -> dict:
    rewards = CRATE_CONFIG[crate_key]["rewards"]
    weights = [reward["weight"] for reward in rewards]
    return random.choices(rewards, weights=weights, k=1)[0]

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
            message = await channel.fetch_message(int(saved["message_id"]))
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
    await ensure_panel_message(guild, "points", points_panel_embed(), PointsView(bot))
    await ensure_panel_message(guild, "ranking", ranking_panel_embed(), RankingView(bot))
    await ensure_panel_message(guild, "xpinfo", xpinfo_panel_embed(), XpInfoView(bot))
    await ensure_panel_message(guild, "shop", shop_embed(), ShopView(bot))

async def process_shop_purchase(interaction: discord.Interaction, item_name: str) -> None:
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await safe_interaction_send(
            interaction,
            content="❌ Kupowanie działa tylko w kanale 🛒・sklep.",
            ephemeral=True
        )
        return

    item_key = item_name.lower().strip()
    item = SHOP_ITEMS.get(item_key)

    if item is None:
        await safe_interaction_send(interaction, content="❌ Nie ma takiego przedmiotu.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    if member is None:
        await safe_interaction_send(interaction, content="❌ Nie udało się znaleźć użytkownika.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, member.id)
    if row is None:
        await safe_interaction_send(interaction, content="❌ Nie masz jeszcze punktów.", ephemeral=True)
        return

    item_price = int(item["price"])
    current_points = int(row["total_points"])

    if current_points < item_price:
        await safe_interaction_send(
            interaction,
            content=f"❌ Za mało punktów. Potrzebujesz **{item_price} pkt**.",
            ephemeral=True
        )
        return

    # Skrzynki
    if item_key in CRATE_CONFIG:
        now_ts = int(time.time())
        next_open_at = get_crate_cooldown(interaction.guild.id, member.id, item_key)
        if next_open_at > now_ts:
            left = next_open_at - now_ts
            await safe_interaction_send(
                interaction,
                content=f"⏳ Ta skrzynka ma cooldown. Spróbuj ponownie za **{left} s**.",
                ephemeral=True
            )
            return

        remove_total_points(interaction.guild.id, member.id, item_price)
        set_crate_cooldown(interaction.guild.id, member.id, item_key, now_ts + CRATE_COOLDOWN_SECONDS)

        reward = choose_crate_reward(item_key)

        if reward["type"] == "points":
            add_points(interaction.guild.id, member.id, int(reward["value"]))
            add_crate_history(interaction.guild.id, member.id, item_key, "points", str(reward["value"]))
            embed = crate_result_embed(item_key, "points", f"{reward['value']:,}".replace(",", " "), member)
            await safe_interaction_send(interaction, embed=embed, ephemeral=True)
            return

        if reward["type"] == "role":
            role = interaction.guild.get_role(int(reward["value"]))
            if role is None:
                add_crate_history(interaction.guild.id, member.id, item_key, "nothing", "brak_roli")
                embed = crate_result_embed(item_key, "nothing", None, member)
                await safe_interaction_send(interaction, embed=embed, ephemeral=True)
                return

            if role in member.roles:
                # jeśli już ma rolę, zamień na punkty pocieszenia
                consolation = 5000
                add_points(interaction.guild.id, member.id, consolation)
                add_crate_history(interaction.guild.id, member.id, item_key, "points", str(consolation))
                embed = discord.Embed(
                    title=f"{CRATE_CONFIG[item_key]['emoji']} Duplikat nagrody",
                    description=f"Miałeś już **{role.name}**, więc dostałeś **{consolation} pkt**.",
                    color=discord.Color.orange(),
                )
                await safe_interaction_send(interaction, embed=embed, ephemeral=True)
                return

            try:
                if role.id == LEGEND_ROLE_ID:
                    vip_role = interaction.guild.get_role(VIP_ROLE_ID)
                    if vip_role and vip_role in member.roles:
                        await member.remove_roles(vip_role, reason="Awans na LEGENDĘ ze skrzynki")

                await member.add_roles(role, reason=f"Skrzynka: {item_key}")
                add_crate_history(interaction.guild.id, member.id, item_key, "role", role.name)
                embed = crate_result_embed(item_key, "role", role.name, member)
                await safe_interaction_send(interaction, embed=embed, ephemeral=True)
                return
            except discord.Forbidden:
                await safe_interaction_send(
                    interaction,
                    content="❌ Bot nie może nadać tej roli. Ustaw rolę bota wyżej.",
                    ephemeral=True
                )
                return

        if reward["type"] == "nothing":
            add_crate_history(interaction.guild.id, member.id, item_key, "nothing", None)
            embed = crate_result_embed(item_key, "nothing", None, member)
            await safe_interaction_send(interaction, embed=embed, ephemeral=True)
            return

    if item_key == "xp_booster":
        now_ts = int(time.time())
        if get_active_xp_boost(interaction.guild.id, member.id) > 1.0:
            await safe_interaction_send(interaction, content="❌ Masz już aktywny booster XP.", ephemeral=True)
            return

        remove_total_points(interaction.guild.id, member.id, item_price)
        set_xp_boost(interaction.guild.id, member.id, 1.25, now_ts + 3600)

        embed = discord.Embed(
            title="⚡ Booster XP aktywowany",
            description="Masz **+25% XP przez 1 godzinę**.",
            color=discord.Color.orange()
        )
        embed.add_field(name="Czas działania", value="1 godzina", inline=False)
        await safe_interaction_send(interaction, embed=embed, ephemeral=True)

        log_embed = discord.Embed(title="⚡ Aktywacja boostera", color=discord.Color.orange())
        log_embed.add_field(name="Użytkownik", value=member.mention, inline=True)
        log_embed.add_field(name="Item", value="⚡ Booster XP 1h", inline=True)
        log_embed.add_field(name="Cena", value=f"{item_price} pkt", inline=True)
        await send_shop_log(interaction.guild, log_embed)
        return

    # Zwykłe itemy sklepowe
    role_id = item.get("role_id")
    role = interaction.guild.get_role(int(role_id)) if role_id else None

    if role_id and role is None:
        await safe_interaction_send(interaction, content="❌ Nie udało się znaleźć roli sklepowej.", ephemeral=True)
        return

    if item_key == "auto_prywatny_kanal":
        try:
            existing_channel = None
            category = discord.utils.get(interaction.guild.categories, name=PRIVATE_CHANNEL_CATEGORY_NAME)
            if category is not None:
                expected_name = sanitize_private_channel_name(member.display_name)
                for ch in category.voice_channels:
                    overwrites = ch.overwrites_for(member)
                    if ch.name == expected_name or overwrites.view_channel is True:
                        existing_channel = ch
                        break
            if existing_channel is not None:
                await safe_interaction_send(
                    interaction,
                    content=f"❌ Masz już prywatny kanał: **{existing_channel.name}**",
                    ephemeral=True,
                )
                return
        except Exception:
            pass
    elif role and role in member.roles:
        await safe_interaction_send(interaction, content="❌ Masz już tę rolę.", ephemeral=True)
        return

    try:
        if role and role.id == LEGEND_ROLE_ID:
            vip_role = interaction.guild.get_role(VIP_ROLE_ID)
            if vip_role and vip_role in member.roles:
                await member.remove_roles(vip_role, reason="Awans na LEGENDĘ")

        created_channel = None

        if item_key == "auto_prywatny_kanal":
            await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")
            created_channel = await create_or_get_private_channel_for_member(interaction.guild, member)
        else:
            if role:
                await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")

        remove_total_points(interaction.guild.id, member.id, item_price)

        embed = discord.Embed(
            title="✅ Zakup udany",
            description=f"Kupiłeś **{item['label']}** za **{item_price} pkt**.",
            color=discord.Color.green()
        )

        if role and role.id == LEGEND_ROLE_ID:
            embed.add_field(name="💎 Bonus Legendy", value="Masz teraz +40% punktów i dostęp do kanałów legendy.", inline=False)
        elif role and role.id == VIP_ROLE_ID:
            embed.add_field(name="⭐ Bonus VIP", value="Masz teraz +20% punktów.", inline=False)
        elif role and role.id == SIGMA_ROLE_ID:
            embed.add_field(name="😎 SIGMA", value="Masz rangę SIGMA.", inline=False)
        elif role and role.id == AURA_ROLE_ID:
            embed.add_field(name="🌌 AURA", value="Masz prestiżową rolę AURA.", inline=False)
        elif item_key == "auto_prywatny_kanal" and created_channel is not None:
            embed.add_field(name="🛠️ Twój kanał", value=f"Gotowe: **{created_channel.name}**", inline=False)

        await safe_interaction_send(interaction, embed=embed, ephemeral=True)

        log_embed = discord.Embed(title="💰 Zakup w sklepie", color=discord.Color.green())
        log_embed.add_field(name="Użytkownik", value=member.mention, inline=True)
        log_embed.add_field(name="Item", value=item["label"], inline=True)
        log_embed.add_field(name="Cena", value=f"{item_price} pkt", inline=True)
        if role is not None:
            log_embed.add_field(name="Rola", value=role.mention, inline=False)
        if item_key == "auto_prywatny_kanal" and created_channel is not None:
            log_embed.add_field(name="Kanał", value=created_channel.name, inline=False)
        await send_shop_log(interaction.guild, log_embed)

    except discord.Forbidden:
        await safe_interaction_send(
            interaction,
            content="❌ Bot nie może nadać tej roli lub utworzyć kanału. Ustaw rolę bota wyżej i daj Manage Channels.",
            ephemeral=True
        )
    except Exception as e:
        await safe_interaction_send(interaction, content=f"❌ Błąd przy zakupie: {e}", ephemeral=True)

# =========================================================
# GUI
# =========================================================
class PointsView(discord.ui.View):
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

class RankingView(discord.ui.View):
    def __init__(self, bot_instance: XPBot):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="🏆 Pokaż ranking", style=discord.ButtonStyle.success, custom_id="xp_ranking_button")
    async def ranking_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        await safe_interaction_send(interaction, embed=ranking_embed(interaction.guild), ephemeral=True)

class XpInfoView(discord.ui.View):
    def __init__(self, bot_instance: XPBot):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="📘 Zasady XP", style=discord.ButtonStyle.secondary, custom_id="xp_info_button")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await safe_interaction_send(interaction, embed=xpinfo_embed(), ephemeral=True)

    @discord.ui.button(label="📜 Historia skrzynek", style=discord.ButtonStyle.primary, custom_id="xp_crate_history_button")
    async def history_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        history = get_last_crate_history(interaction.guild.id, interaction.user.id, 5)
        await safe_interaction_send(interaction, embed=crate_history_embed(interaction.user, history), ephemeral=True)

class ShopView(discord.ui.View):
    def __init__(self, bot_instance: XPBot):
        super().__init__(timeout=None)
        self.bot = bot_instance

    @discord.ui.button(label="Zwykła", emoji="📦", style=discord.ButtonStyle.secondary, custom_id="shop_crate_basic", row=0)
    async def buy_crate_basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "crate_basic")

    @discord.ui.button(label="Mystery", emoji="🎰", style=discord.ButtonStyle.secondary, custom_id="shop_crate_mystery", row=0)
    async def buy_crate_mystery(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "crate_mystery")

    @discord.ui.button(label="Booster XP", emoji="⚡", style=discord.ButtonStyle.primary, custom_id="shop_xp_booster", row=0)
    async def buy_xp_booster(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "xp_booster")

    @discord.ui.button(label="Premium", emoji="🎁", style=discord.ButtonStyle.secondary, custom_id="shop_crate_premium", row=0)
    async def buy_crate_premium(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "crate_premium")

    @discord.ui.button(label="Auto kanał", emoji="🛠️", style=discord.ButtonStyle.primary, custom_id="shop_auto_private_channel", row=0)
    async def buy_auto_private_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "auto_prywatny_kanal")

    @discord.ui.button(label="SIGMA", emoji="😎", style=discord.ButtonStyle.secondary, custom_id="shop_sigma", row=1)
    async def buy_sigma(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "sigma")

    @discord.ui.button(label="AURA", emoji="🌌", style=discord.ButtonStyle.secondary, custom_id="shop_aura", row=1)
    async def buy_aura(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "aura")

    @discord.ui.button(label="VIP", emoji="⭐", style=discord.ButtonStyle.success, custom_id="shop_vip", row=1)
    async def buy_vip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "vip")

    @discord.ui.button(label="Legendarna", emoji="💎", style=discord.ButtonStyle.primary, custom_id="shop_crate_legendary", row=1)
    async def buy_crate_legendary(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "crate_legendary")

    @discord.ui.button(label="LEGENDA", emoji="💎", style=discord.ButtonStyle.danger, custom_id="shop_legenda", row=1)
    async def buy_legenda(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "legenda")

# =========================================================
# EVENTY
# =========================================================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return
    if not message.content or not message.content.strip():
        return

    count = update_message_count(message.guild.id, message.author.id)

    if count % TEXT_MESSAGES_REQUIRED == 0:
        member = message.guild.get_member(message.author.id)
        if member:
            add_points_with_role_bonus(member, text_points=TEXT_POINTS)

@bot.event
async def on_member_join(member: discord.Member):
    if not is_real_user(member):
        return

    embed = discord.Embed(title="📥 Dołączenie na serwer", color=discord.Color.green())
    embed.add_field(name="Użytkownik", value=f"{member.mention} ({member.id})", inline=False)
    embed.add_field(name="Konto utworzone", value=f"<t:{int(member.created_at.timestamp())}:F>", inline=False)
    await send_admin_log(member.guild, embed)

@bot.event
async def on_member_remove(member: discord.Member):
    if not is_real_user(member):
        return

    guild = member.guild
    bot.vc_active_since.pop((guild.id, member.id), None)

    moderator, reason = await get_recent_audit_actor_and_reason(
        guild,
        discord.AuditLogAction.kick,
        member.id
    )

    delete_user_data(guild.id, member.id)

    if moderator and moderator.bot:
        return

    if moderator:
        embed = discord.Embed(title="👢 Wyrzucenie z serwera", color=discord.Color.red())
        embed.add_field(name="Kogo wyrzucono", value=f"{member} ({member.id})", inline=False)
        embed.add_field(name="Kto wyrzucił", value=moderator.mention, inline=False)
        if reason:
            embed.add_field(name="Powód", value=reason, inline=False)
        else:
            embed.add_field(name="Powód", value="brak", inline=False)
        await send_admin_log(guild, embed)
        return

    embed = discord.Embed(title="📤 Wyjście z serwera", color=discord.Color.orange())
    embed.add_field(name="Użytkownik", value=f"{member} ({member.id})", inline=False)
    await send_admin_log(guild, embed)

@bot.event
async def on_member_ban(guild: discord.Guild, user: discord.User):
    if not is_real_user(user):
        return

    delete_user_data(guild.id, user.id)
    bot.vc_active_since.pop((guild.id, user.id), None)

    moderator, reason = await get_recent_audit_actor_and_reason(guild, discord.AuditLogAction.ban, user.id)
    embed = discord.Embed(title="🔨 Ban + usunięto dane punktów", color=discord.Color.dark_red())
    embed.add_field(name="Kogo zbanowano", value=f"{user} ({user.id})", inline=False)
    if moderator:
        embed.add_field(name="Kto zbanował", value=f"{moderator.mention}", inline=False)
    embed.add_field(name="Powód", value=reason or "brak", inline=False)
    embed.add_field(name="Dane", value="Usunięto z rankingu i systemu XP", inline=False)
    await send_admin_log(guild, embed)

@bot.event
async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
    key = (member.guild.id, member.id)

    if is_active_for_vc(member):
        if key not in bot.vc_active_since:
            bot.vc_active_since[key] = time.time()
    else:
        bot.vc_active_since.pop(key, None)

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")
    if USING_POSTGRES:
        print("🔥 Używam PostgreSQL")
    else:
        print(f"⚠️ Używam SQLite: {SQLITE_DB_FILE}")

    for guild in bot.guilds:
        for member in guild.members:
            if is_active_for_vc(member):
                bot.vc_active_since[(guild.id, member.id)] = time.time()

        await refresh_all_panels(guild)

    if not vc_loop.is_running():
        vc_loop.start()

    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print(f"Błąd synchronizacji komend: {e}")

# =========================================================
# VC LOOP
# =========================================================
@tasks.loop(seconds=10)
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

        if active_count <= 1:
            points_per_interval = VC_POINTS_SOLO
        else:
            points_per_interval = active_count

        add_points_with_role_bonus(member, voice_points=full_intervals * points_per_interval)
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

    await safe_interaction_send(interaction, embed=embed, ephemeral=True)

@bot.tree.command(name="ranking", description="Pokazuje ranking serwera")
async def ranking(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != RANKING_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 🏆・ranking.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=ranking_embed(interaction.guild))

@bot.tree.command(name="xpinfo", description="Pokazuje zasady punktów")
async def xpinfo(interaction: discord.Interaction):
    if interaction.channel_id != XPINFO_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 📘・info-xp.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=xpinfo_embed())

@bot.tree.command(name="sklep", description="Pokazuje sklep punktów")
async def sklep(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await safe_interaction_send(interaction, content="❌ Użyj tej komendy w kanale 🛒・sklep.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=shop_embed(), view=ShopView(bot))

@bot.tree.command(name="kup", description="Kup przedmiot ze sklepu")
@app_commands.describe(przedmiot="np. crate_basic, crate_mystery, xp_booster, crate_premium, auto_prywatny_kanal, sigma, aura, vip, crate_legendary, legenda")
async def kup(interaction: discord.Interaction, przedmiot: str):
    await process_shop_purchase(interaction, przedmiot)

@bot.tree.command(name="skrzynki_historia", description="Pokazuje ostatnie otwarcia skrzynek")
async def skrzynki_historia(interaction: discord.Interaction):
    if interaction.guild is None or not isinstance(interaction.user, discord.Member):
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    history = get_last_crate_history(interaction.guild.id, interaction.user.id, 5)
    await safe_interaction_send(interaction, embed=crate_history_embed(interaction.user, history), ephemeral=True)

@bot.tree.command(name="odswiez_panele", description="Odświeża wszystkie panele bota")
@app_commands.checks.has_permissions(manage_guild=True)
async def odswiez_panele(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await refresh_all_panels(interaction.guild)
    await safe_interaction_send(interaction, content="✅ Panele zostały odświeżone.", ephemeral=True)

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        if isinstance(error, app_commands.MissingPermissions):
            await safe_interaction_send(interaction, content="❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        else:
            await safe_interaction_send(interaction, content=f"❌ Błąd komendy: {error}", ephemeral=True)
    except discord.InteractionResponded:
        await interaction.followup.send(f"❌ Błąd komendy: {error}", ephemeral=True)

# =========================================================
# START
# =========================================================
def main() -> None:
    if not TOKEN:
        raise RuntimeError("Brak zmiennej TOKEN.")
    init_db()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()

@bot.event
async def on_member_remove(member: discord.Member):
    if not is_real_user(member):
        return

    guild = member.guild

    moderator, reason = await get_recent_audit_actor_and_reason(
        guild,
        discord.AuditLogAction.kick,
        member.id
    )

    if moderator and moderator.bot:
        return

    # reset punktów
    reset_user_points(guild.id, member.id)

    embed = discord.Embed(title="👢 Kick + reset punktów", color=discord.Color.red())
    embed.add_field(name="Użytkownik", value=f"{member} ({member.id})", inline=False)

    if moderator:
        embed.add_field(name="Moderator", value=moderator.mention, inline=False)

    embed.add_field(name="Punkty", value="Wyzerowane", inline=False)

    if reason:
        embed.add_field(name="Powód", value=reason, inline=False)

    await send_admin_log(guild, embed)
