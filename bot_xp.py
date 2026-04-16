import os
import asyncio
import random
import time
import re
import json
import unicodedata
from datetime import datetime, timezone, timedelta
from typing import Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import discord
from discord import app_commands
from discord.ext import commands, tasks

# =========================================================
# KONFIG
# =========================================================
TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

FOOTBALL_DATA_API_KEY = os.getenv("FOOTBALL_DATA_API_KEY", "")
FOOTBALL_DATA_COMPETITIONS = [x.strip().upper() for x in os.getenv("FOOTBALL_DATA_COMPETITIONS", "PL,PD,BL1,SA,CL").split(",") if x.strip()]
AUTO_FETCH_MATCHES_ENABLED = os.getenv("AUTO_FETCH_MATCHES_ENABLED", "true").lower() in {"1", "true", "yes", "on"}
AUTO_FETCH_LOOKAHEAD_DAYS = int(os.getenv("AUTO_FETCH_LOOKAHEAD_DAYS", "7"))
AUTO_FETCH_INTERVAL_MINUTES = int(os.getenv("AUTO_FETCH_INTERVAL_MINUTES", "15"))
LIVE_RESULTS_LIMIT = int(os.getenv("LIVE_RESULTS_LIMIT", "10"))

# =========================================================
# ID KANAŁÓW
# =========================================================
POINTS_CHANNEL_ID = 1490629053286191206      # 📊・sprawdz-punkty
RANKING_CHANNEL_ID = 1490629324305600594     # 🏆・ranking
XPINFO_CHANNEL_ID = 1490629632796524554      # 📘・info-xp
SHOP_CHANNEL_ID = 1490648124006338640        # 🛒・sklep
BETTING_CHANNEL_ID = 1487496845176606821     # 🤑・obstawianie-meczy
BETTING_LIVE_CHANNEL_ID = int(os.getenv("BETTING_LIVE_CHANNEL_ID", "1487496845176606821"))

BETTING_CATEGORY_NAME = "🎯 OBSTAWIANIE"
BETTING_AUTO_CHANNELS = {
    "betting": "🎯・panel",
    "betting_live": "🔴・live",
    "betting_bets": "🧾・typy",
    "betting_ranking": "🥇・ranking",
    "betting_stats": "📊・staty",
}

LEGEND_TEXT_CHANNEL_ID = 1490791025671803013 # 💎・legenda-czat
LEGEND_VC_CHANNEL_ID = 1490792255504646407   # 💎・Legenda VC
SHOP_LOG_CHANNEL_ID = 1491934996745683035      # 📜・logi-pod-sklep
ADMIN_LOG_CHANNEL_ID = 1491944667124596836     # 📜・logi-administracyjne

AUTOMOD_ENABLED = True
AUTOMOD_DELETE_AND_WARN = True
AUTOMOD_WARNING_DELETE_AFTER = 8
AUTOMOD_WARN_TIMEOUTS = {
    3: 10,
    5: 60,
    7: 1440,
}
AUTOMOD_WARN_DECAY_HOURS = 24
AUTOMOD_WARN_KICK_AT = 10
AUTOMOD_WARN_BAN_AT = 20
AUTOMOD_BAN_DISCORD_INVITES = True
AUTOMOD_BLOCK_EXTERNAL_LINKS = True
AUTOMOD_SHORTENER_WARN = True

AUTOMOD_BLOCKED_LINK_KEYWORDS = {
    "tiktok.com",
    "vt.tiktok.com",
    "vm.tiktok.com",
    "youtube.com",
    "youtu.be",
    "kick.com",
}

AUTOMOD_SHORTENER_KEYWORDS = {
    "bit.ly",
    "tinyurl.com",
    "t.co",
    "cutt.ly",
    "shorturl.at",
    "goo.gl",
    "rb.gy",
    "rebrand.ly",
    "ow.ly",
    "is.gd",
    "buff.ly",
}

BETTING_MIN_STAKE = 10
BETTING_MAX_OPEN_MATCHES_PER_GUILD = 50
AUTO_DEFAULT_ODDS_HOME = 2.20
AUTO_DEFAULT_ODDS_DRAW = 3.20
AUTO_DEFAULT_ODDS_AWAY = 2.20

AUTOMOD_EXCLUDED_CHANNEL_IDS = {
    POINTS_CHANNEL_ID,
    RANKING_CHANNEL_ID,
    XPINFO_CHANNEL_ID,
    SHOP_CHANNEL_ID,
    SHOP_LOG_CHANNEL_ID,
    ADMIN_LOG_CHANNEL_ID,
}
AUTOMOD_CHANNEL_NAME_KEYWORDS = {
    "chat", "czat", "general", "glowny", "główny", "ogolny", "ogólny", "lobby"
}
AUTOMOD_BAD_PATTERNS = [
    r"\bkurw[a-ząćęłńóśźż]*\b",
    r"\bkurw[oaeuyąę]*\b",
    r"\bskurw[a-ząćęłńóśźż]*\b",
    r"\bskurwysyn[a-ząćęłńóśźż]*\b",

    r"\bjeb[a-ząćęłńóśźż]*\b",
    r"\bjeba[cć]\b",
    r"\bjebac\b",
    r"\bjeba[cć][a-ząćęłńóśźż]*\b",
    r"\bjebie[a-ząćęłńóśźż]*\b",
    r"\bjeban[a-ząćęłńóśźż]*\b",
    r"\bjebnięt[a-ząćęłńóśźż]*\b",
    r"\bdojeb[a-ząćęłńóśźż]*\b",
    r"\bodjeb[a-ząćęłńóśźż]*\b",
    r"\bprzejeb[a-ząćęłńóśźż]*\b",
    r"\bwyjeb[a-ząćęłńóśźż]*\b",
    r"\bpojeb[a-ząćęłńóśźż]*\b",

    r"\bpierdol[a-ząćęłńóśźż]*\b",
    r"\bpierdole[a-ząćęłńóśźż]*\b",
    r"\bpierdoli[a-ząćęłńóśźż]*\b",
    r"\bpierdolic\b",
    r"\bpierdoli[cć]\b",
    r"\bspierdal[a-ząćęłńóśźż]*\b",
    r"\bwypierdal[a-ząćęłńóśźż]*\b",
    r"\bnapierdal[a-ząćęłńóśźż]*\b",
    r"\bopierdal[a-ząćęłńóśźż]*\b",
    r"\bwpierdol[a-ząćęłńóśźż]*\b",
    r"\bwkurw[a-ząćęłńóśźż]*\b",
    r"\bwkurwic\b",
    r"\bwkurwic\s+sie\b",
    r"\brozpierdol[a-ząćęłńóśźż]*\b",
    r"\brozpierdoli[mnwyćcsząężźłó]*\b",

    r"\bchuj[a-ząćęłńóśźż]*\b",
    r"\bchuja\b",
    r"\bchuju\b",
    r"\bchujem\b",
    r"\bchujow[a-ząćęłńóśźż]*\b",
    r"\bchujni[a-ząćęłńóśźż]*\b",
    r"\bch[óo]j[a-ząćęłńóśźż]*\b",
    r"\bchuje\b",

    r"\bcip[a-ząćęłńóśźż]*\b",
    r"\bcipa\b",
    r"\bcipk[a-ząćęłńóśźż]*\b",
    r"\bcipcz[a-ząćęłńóśźż]*\b",

    r"\bpizd[a-ząćęłńóśźż]*\b",
    r"\bpizda\b",
    r"\bpizdo\b",
    r"\bspizg[a-ząćęłńóśźż]*\b",

    r"\bsuk[a-ząćęłńóśźż]*\b",
    r"\bsuko\b",
    r"\bsucz[a-ząćęłńóśźż]*\b",

    r"\bdziwk[a-ząćęłńóśźż]*\b",
    r"\bdziwki\b",
    r"\bdz1wka\b",
    r"\bkurtyzan[a-ząćęłńóśźż]*\b",

    r"\bfiut[a-ząćęłńóśźż]*\b",
    r"\bfiucie\b",
    r"\bkutas[a-ząćęłńóśźż]*\b",
    r"\bcwel[a-ząćęłńóśźż]*\b",
    r"\bcwele\b",
    r"\bpa[lł]a\b",
    r"\bpa[lł]o\b",

    r"\bdebil[a-ząćęłńóśźż]*\b",
    r"\buposledzeniec\b",
    r"\bupo[sś]\b",
    r"\bniepelnosprawny\b",
    r"\bniepelnosprawna\b",
    r"\bidiot[a-ząćęłńóśźż]*\b",
    r"\bimbecyl[a-ząćęłńóśźż]*\b",
    r"\bkretyn[a-ząćęłńóśźż]*\b",
    r"\bbaran[a-ząćęłńóśźż]*\b",
    r"\bmato[lł][a-ząćęłńóśźż]*\b",
    r"\bprzyglup[a-ząćęłńóśźż]*\b",
    r"\bt[eę]pak[a-ząćęłńóśźż]*\b",
    r"\bmongol[a-ząćęłńóśźż]*\b",
    r"\bdown[a-ząćęłńóśźż]*\b",

    r"\bzjeb[a-ząćęłńóśźż]*\b",
    r"\bzjeba\b",
    r"\bzjebie\b",
    r"\bzjeby\b",
    r"\bobsrany\b",
    r"\bobsran[a-ząćęłńóśźż]*\b",
    r"\bśmie[cć][a-ząćęłńóśźż]*\b",
    r"\bsmiec[a-ząćęłńóśźż]*\b",
    r"\bszmata[a-ząćęłńóśźż]*\b",
    r"\bszmaty\b",
    r"\bgn[óo]j[a-ząćęłńóśźż]*\b",
    r"\bpadlin[a-ząćęłńóśźż]*\b",
    r"\btrupie\b",
    r"\bkongo\b",
    r"\bkng\b",
    r"\bdupa\b",
    r"\bmorda\b",
    r"\bpedal[a-ząćęłńóśźż]*\b",
    r"\bpeda[lł][a-ząćęłńóśźż]*\b",
]

AUTOMOD_THREAT_PATTERNS = [
    r"\bzabij[eę]\s+ci[eę]\b",
    r"\bzajebi[eę]\s+ci[eę]\b",
    r"\brozjeb[ięe]\s+ci[eę]\b",
    r"\bwpierdol[eę]\s+ci\b",
    r"\bdojad[eę]\s+ci[eę]\b",
    r"\bdorw[eę]\s+ci[eę]\b",
    r"\bpo[łl]ami[eę]\s+ci[eę]\b",
    r"\bpobij[eę]\s+ci[eę]\b",
    r"\bspal[eę]\s+ci\b",
    r"\bznajd[eę]\s+ci[eę]\b",
    r"\bmasz\s+przejeban[eą]\b",
    r"\brozpierdolimy\b",
    r"\brozjebiemy\b",
    r"\bdojedziemy\b",
]
AUTOMOD_INSULT_PATTERNS = [
    r"\bty\s+debil[uoa]?\b",
    r"\bty\s+idiot[oau]?\b",
    r"\bty\s+kretyni[eauo]?\b",
    r"\bty\s+zjeb[ieuao]?\b",
    r"\bty\s+chuju\b",
    r"\bty\s+kurwo\b",
    r"\bty\s+szmato\b",
    r"\bty\s+smiec[iu]?\b",
    r"\bjestes\s+nikim\b",
    r"\btwoja\s+stara\b",

    # obraźliwe użycia wobec orientacji - blokujemy tylko jako wyzwisko, nie neutralne słowo
    r"\bty\s+gej[uoa]?\b",
    r"\bjebany\s+gej\b",
    r"\bpieprzony\s+gej\b",
    r"\bbrudny\s+gej\b",
    r"\bstary\b",
    r"\btwoj\s+stary\b",
    r"\btwojka\s+stara\b",

    # obrażanie rodziców i rodziny
    r"\bjebac\s+twoja\s+matke\b",
    r"\bjebac\s+twoja\s+stara\b",
    r"\bkurwa\s+twoja\s+matka\b",
    r"\btwoja\s+matka\s+to\b",
    r"\btwoj\s+stary\s+to\b",
    r"\bjebac\s+twojego\s+starego\b",
    r"\bpojebana\s+rodzina\b",
    r"\bjebana\s+rodzina\b",
    r"\btwoja\s+rodzina\s+to\b",
    r"\bmatke\s+ci\s+jebac\b",
    r"\bstara\s+kurwa\b",
    r"\bwalony\s+w\s+dupe\b",
    r"\bwalony\s+w\s+dupa\b",
    r"\bwalony\s+w\s+dupie\b",
    r"\bw\s+dupe\b",
    r"\bw\s+dupa\b",
    r"\bw\s+dupie\b",
    r"\bmorda\b",
    r"\bcwel\b",
    r"\bcwele\b",
    r"\bpedal\b",
    r"\bpeda[lł]\b",
]

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
    "betting": BETTING_CHANNEL_ID,
    "betting_live": BETTING_LIVE_CHANNEL_ID,
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
            CREATE TABLE IF NOT EXISTS automod_warnings (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                warning_count INTEGER NOT NULL DEFAULT 0,
                last_reason TEXT,
                updated_at BIGINT NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_matches (
                match_id BIGSERIAL PRIMARY KEY,
                guild_id BIGINT NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                start_ts BIGINT NOT NULL,
                odds_home REAL NOT NULL,
                odds_draw REAL NOT NULL,
                odds_away REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                result TEXT,
                created_by BIGINT NOT NULL,
                created_at BIGINT NOT NULL,
                source TEXT DEFAULT 'manual',
                external_id TEXT,
                auto_created INTEGER DEFAULT 0,
                competition_code TEXT,
                competition_name TEXT,
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                live_status TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_bets (
                guild_id BIGINT NOT NULL,
                match_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                pick TEXT NOT NULL,
                stake INTEGER NOT NULL,
                potential_win INTEGER NOT NULL,
                created_at BIGINT NOT NULL,
                PRIMARY KEY (guild_id, match_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_user_stats (
                guild_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                total_bets INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                total_staked BIGINT NOT NULL DEFAULT 0,
                total_won BIGINT NOT NULL DEFAULT 0,
                current_streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                biggest_win BIGINT NOT NULL DEFAULT 0,
                best_odds REAL NOT NULL DEFAULT 0,
                updated_at BIGINT NOT NULL DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
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
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_moderation (
                guild_id BIGINT PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1
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
            CREATE TABLE IF NOT EXISTS automod_warnings (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                warning_count INTEGER NOT NULL DEFAULT 0,
                last_reason TEXT,
                updated_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                start_ts INTEGER NOT NULL,
                odds_home REAL NOT NULL,
                odds_draw REAL NOT NULL,
                odds_away REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                result TEXT,
                created_by INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                source TEXT DEFAULT 'manual',
                external_id TEXT,
                auto_created INTEGER DEFAULT 0,
                competition_code TEXT,
                competition_name TEXT,
                home_score INTEGER DEFAULT 0,
                away_score INTEGER DEFAULT 0,
                live_status TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_bets (
                guild_id INTEGER NOT NULL,
                match_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                pick TEXT NOT NULL,
                stake INTEGER NOT NULL,
                potential_win INTEGER NOT NULL,
                created_at INTEGER NOT NULL,
                PRIMARY KEY (guild_id, match_id, user_id)
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS betting_user_stats (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total_bets INTEGER NOT NULL DEFAULT 0,
                wins INTEGER NOT NULL DEFAULT 0,
                losses INTEGER NOT NULL DEFAULT 0,
                total_staked INTEGER NOT NULL DEFAULT 0,
                total_won INTEGER NOT NULL DEFAULT 0,
                current_streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                biggest_win INTEGER NOT NULL DEFAULT 0,
                best_odds REAL NOT NULL DEFAULT 0,
                updated_at INTEGER NOT NULL DEFAULT 0,
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
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                crate_key TEXT NOT NULL,
                reward_type TEXT NOT NULL,
                reward_value TEXT,
                created_at INTEGER NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS chat_moderation (
                guild_id INTEGER PRIMARY KEY,
                enabled INTEGER NOT NULL DEFAULT 1
            )
        """)

    conn.commit()
    conn.close()
    ensure_betting_schema_migrations()


def ensure_betting_schema_migrations() -> None:
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual'")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS external_id TEXT")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS auto_created INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS competition_code TEXT")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS competition_name TEXT")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS home_score INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS away_score INTEGER DEFAULT 0")
        cur.execute("ALTER TABLE betting_matches ADD COLUMN IF NOT EXISTS live_status TEXT")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_betting_matches_guild_external ON betting_matches (guild_id, external_id)")
        cur.execute("ALTER TABLE betting_user_stats ADD COLUMN IF NOT EXISTS biggest_win BIGINT DEFAULT 0")
        cur.execute("ALTER TABLE betting_user_stats ADD COLUMN IF NOT EXISTS best_odds REAL DEFAULT 0")
    else:
        cur.execute("PRAGMA table_info(betting_matches)")
        cols = {row[1] for row in cur.fetchall()}
        for statement in [
            ("source", "ALTER TABLE betting_matches ADD COLUMN source TEXT DEFAULT 'manual'"),
            ("external_id", "ALTER TABLE betting_matches ADD COLUMN external_id TEXT"),
            ("auto_created", "ALTER TABLE betting_matches ADD COLUMN auto_created INTEGER DEFAULT 0"),
            ("competition_code", "ALTER TABLE betting_matches ADD COLUMN competition_code TEXT"),
            ("competition_name", "ALTER TABLE betting_matches ADD COLUMN competition_name TEXT"),
            ("home_score", "ALTER TABLE betting_matches ADD COLUMN home_score INTEGER DEFAULT 0"),
            ("away_score", "ALTER TABLE betting_matches ADD COLUMN away_score INTEGER DEFAULT 0"),
            ("live_status", "ALTER TABLE betting_matches ADD COLUMN live_status TEXT"),
        ]:
            if statement[0] not in cols:
                cur.execute(statement[1])

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

    cur.execute(sql("""
        DELETE FROM automod_warnings
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))

    conn.commit()
    conn.close()


def expire_automod_warnings(guild_id: int, user_id: int) -> None:
    now_ts = int(time.time())
    decay_seconds = AUTOMOD_WARN_DECAY_HOURS * 3600

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT warning_count, updated_at
        FROM automod_warnings
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)

    if row:
        warning_count = int(row["warning_count"])
        last_update = int(row["updated_at"])
        elapsed = now_ts - last_update

        if elapsed >= decay_seconds:
            decay_steps = elapsed // decay_seconds
            new_count = max(0, warning_count - int(decay_steps))

            if new_count <= 0:
                cur.execute(sql("""
                    DELETE FROM automod_warnings
                    WHERE guild_id = ? AND user_id = ?
                """), (guild_id, user_id))
            else:
                refreshed_at = last_update + int(decay_steps) * decay_seconds
                cur.execute(sql("""
                    UPDATE automod_warnings
                    SET warning_count = ?,
                        updated_at = ?
                    WHERE guild_id = ? AND user_id = ?
                """), (new_count, refreshed_at, guild_id, user_id))
            conn.commit()

    conn.close()


def get_automod_warning_count(guild_id: int, user_id: int) -> int:
    expire_automod_warnings(guild_id, user_id)

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT warning_count
        FROM automod_warnings
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)
    conn.close()
    return int(row["warning_count"]) if row else 0


def add_automod_warning(guild_id: int, user_id: int, reason: str) -> int:
    expire_automod_warnings(guild_id, user_id)
    now_ts = int(time.time())
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO automod_warnings (guild_id, user_id, warning_count, last_reason, updated_at)
            VALUES (%s, %s, 1, %s, %s)
            ON CONFLICT (guild_id, user_id)
            DO UPDATE SET
                warning_count = automod_warnings.warning_count + 1,
                last_reason = EXCLUDED.last_reason,
                updated_at = EXCLUDED.updated_at
        """, (guild_id, user_id, reason, now_ts))
    else:
        cur.execute("""
            INSERT OR IGNORE INTO automod_warnings (guild_id, user_id, warning_count, last_reason, updated_at)
            VALUES (?, ?, 0, ?, ?)
        """, (guild_id, user_id, reason, now_ts))
        cur.execute("""
            UPDATE automod_warnings
            SET warning_count = warning_count + 1,
                last_reason = ?,
                updated_at = ?
            WHERE guild_id = ? AND user_id = ?
        """, (reason, now_ts, guild_id, user_id))

    cur.execute(sql("""
        SELECT warning_count
        FROM automod_warnings
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)
    conn.commit()
    conn.close()
    return int(row["warning_count"]) if row else 1


def clear_automod_warnings(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        DELETE FROM automod_warnings
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    conn.commit()
    conn.close()

def is_chat_moderation_enabled(guild_id: int) -> bool:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT enabled
        FROM chat_moderation
        WHERE guild_id = ?
    """), (guild_id,))
    row = fetchone_dict(cur)
    conn.close()

    if row is None:
        return True
    return bool(int(row["enabled"]))


def set_chat_moderation_enabled(guild_id: int, enabled: bool) -> None:
    conn = db_connect()
    cur = conn.cursor()

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO chat_moderation (guild_id, enabled)
            VALUES (%s, %s)
            ON CONFLICT (guild_id)
            DO UPDATE SET enabled = EXCLUDED.enabled
        """, (guild_id, int(enabled)))
    else:
        cur.execute("""
            INSERT OR REPLACE INTO chat_moderation (guild_id, enabled)
            VALUES (?, ?)
        """, (guild_id, int(enabled)))

    conn.commit()
    conn.close()


def chat_moderation_status_text(guild_id: int) -> str:
    return "🟢 WŁĄCZONA" if is_chat_moderation_enabled(guild_id) else "🔴 WYŁĄCZONA"



def ensure_typer_stats_row(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    now_ts = int(time.time())
    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO betting_user_stats (
                guild_id, user_id, total_bets, wins, losses, total_staked, total_won,
                current_streak, best_streak, biggest_win, best_odds, updated_at
            ) VALUES (%s, %s, 0, 0, 0, 0, 0, 0, 0, 0, 0, %s)
            ON CONFLICT (guild_id, user_id) DO NOTHING
        """, (guild_id, user_id, now_ts))
    else:
        cur.execute("""
            INSERT OR IGNORE INTO betting_user_stats (
                guild_id, user_id, total_bets, wins, losses, total_staked, total_won,
                current_streak, best_streak, biggest_win, best_odds, updated_at
            ) VALUES (?, ?, 0, 0, 0, 0, 0, 0, 0, 0, 0, ?)
        """, (guild_id, user_id, now_ts))
    conn.commit()
    conn.close()


def register_bet_placed(guild_id: int, user_id: int, stake: int, odds: float) -> None:
    ensure_typer_stats_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE betting_user_stats
        SET total_bets = total_bets + 1,
            total_staked = total_staked + ?,
            best_odds = CASE WHEN ? > COALESCE(best_odds, 0) THEN ? ELSE best_odds END,
            updated_at = ?
        WHERE guild_id = ? AND user_id = ?
    """), (int(stake), float(odds), float(odds), int(time.time()), guild_id, user_id))
    conn.commit()
    conn.close()


def register_bet_settlement(guild_id: int, user_id: int, *, won: bool, payout: int) -> None:
    ensure_typer_stats_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    now_ts = int(time.time())
    cur.execute(sql("""
        SELECT wins, losses, current_streak, best_streak
        FROM betting_user_stats
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur) or {"wins": 0, "losses": 0, "current_streak": 0, "best_streak": 0}

    wins = int(row["wins"])
    losses = int(row["losses"])
    current_streak = int(row["current_streak"])
    best_streak = int(row["best_streak"])

    if won:
        wins += 1
        current_streak += 1
        best_streak = max(best_streak, current_streak)
        cur.execute(sql("""
            UPDATE betting_user_stats
            SET wins = ?,
                total_won = total_won + ?,
                biggest_win = CASE WHEN ? > COALESCE(biggest_win, 0) THEN ? ELSE biggest_win END,
                current_streak = ?,
                best_streak = ?,
                updated_at = ?
            WHERE guild_id = ? AND user_id = ?
        """), (wins, int(payout), int(payout), int(payout), current_streak, best_streak, now_ts, guild_id, user_id))
    else:
        losses += 1
        current_streak = 0
        cur.execute(sql("""
            UPDATE betting_user_stats
            SET losses = ?,
                current_streak = 0,
                updated_at = ?
            WHERE guild_id = ? AND user_id = ?
        """), (losses, now_ts, guild_id, user_id))

    conn.commit()
    conn.close()


def get_typer_stats_row(guild_id: int, user_id: int) -> dict | None:
    ensure_typer_stats_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_user_stats
        WHERE guild_id = ? AND user_id = ?
    """), (guild_id, user_id))
    row = fetchone_dict(cur)
    conn.close()
    return row


def get_top_typers(guild_id: int, limit: int = 10) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_user_stats
        WHERE guild_id = ?
        ORDER BY total_won DESC, wins DESC, best_streak DESC, total_bets DESC
        LIMIT ?
    """), (guild_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_match_by_external_id(guild_id: int, external_id: str) -> dict | None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_matches
        WHERE guild_id = ? AND external_id = ?
        LIMIT 1
    """), (guild_id, external_id))
    row = fetchone_dict(cur)
    conn.close()
    return row


def update_match_scores_and_status(guild_id: int, match_id: int, home_score, away_score, live_status: str, local_status: str) -> None:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(sql("""
        SELECT home_score, away_score
        FROM betting_matches
        WHERE guild_id = ? AND match_id = ?
    """), (guild_id, match_id))
    current = fetchone_dict(cur) or {"home_score": None, "away_score": None}

    final_home = int(home_score) if home_score is not None else current.get("home_score")
    final_away = int(away_score) if away_score is not None else current.get("away_score")

    cur.execute(sql("""
        UPDATE betting_matches
        SET home_score = ?,
            away_score = ?,
            live_status = ?,
            status = CASE WHEN status = 'settled' THEN status ELSE ? END
        WHERE guild_id = ? AND match_id = ?
    """), (final_home, final_away, live_status, local_status, guild_id, match_id))
    conn.commit()
    conn.close()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def fetch_remote_json(url: str, headers: dict[str, str]) -> dict:
    req = Request(url, headers=headers)
    with urlopen(req, timeout=20) as response:
        payload = response.read().decode("utf-8")
    return json.loads(payload)


def fetch_competition_standings(competition_code: str) -> dict:
    if not FOOTBALL_DATA_API_KEY:
        return {}

    try:
        data = fetch_remote_json(
            f"https://api.football-data.org/v4/competitions/{competition_code}/standings",
            {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
        )
    except Exception:
        return {}

    positions = {}
    for standing in data.get("standings", []):
        for row in standing.get("table", []):
            team = row.get("team") or {}
            name = team.get("shortName") or team.get("name")
            if name:
                positions[name] = int(row.get("position") or 99)
    return positions


def derive_realistic_odds(home_team: str, away_team: str, competition_code: str) -> tuple[float, float, float]:
    positions = fetch_competition_standings(competition_code)
    home_pos = positions.get(home_team, 10)
    away_pos = positions.get(away_team, 10)

    # niższa pozycja = mocniejsza drużyna
    home_strength = max(1.0, 25.0 - float(home_pos))
    away_strength = max(1.0, 25.0 - float(away_pos))

    # premia gospodarza
    home_strength += 2.0

    total = home_strength + away_strength
    home_prob = home_strength / total
    away_prob = away_strength / total

    closeness = abs(home_prob - away_prob)
    draw_prob = clamp(0.22 + (0.12 - closeness * 0.25), 0.18, 0.34)

    remaining = max(0.50, 1.0 - draw_prob)
    home_prob = (home_prob / (home_prob + away_prob)) * remaining
    away_prob = (away_prob / (home_prob + away_prob)) * remaining if (home_prob + away_prob) > 0 else remaining / 2

    margin = 1.08
    odds_home = clamp(round((1 / max(0.08, home_prob)) * margin, 2), 1.35, 6.5)
    odds_draw = clamp(round((1 / max(0.08, draw_prob)) * margin, 2), 2.2, 6.5)
    odds_away = clamp(round((1 / max(0.08, away_prob)) * margin, 2), 1.35, 6.5)

    return odds_home, odds_draw, odds_away


def normalize_api_result_to_pick(winner: str | None) -> str | None:
    if winner == "HOME_TEAM":
        return "1"
    if winner == "DRAW":
        return "X"
    if winner == "AWAY_TEAM":
        return "2"
    return None


def derive_result_from_scores(home_score, away_score) -> str | None:
    if home_score is None or away_score is None:
        return None
    if int(home_score) > int(away_score):
        return "1"
    if int(home_score) == int(away_score):
        return "X"
    return "2"


def extract_api_final_scores(item: dict) -> tuple[int | None, int | None]:
    score = (item.get("score") or {})
    for key in ("fullTime", "extraTime", "regularTime", "penalties", "halfTime"):
        block = score.get(key) or {}
        home_raw = block.get("home")
        away_raw = block.get("away")
        if home_raw is not None and away_raw is not None:
            try:
                return int(home_raw), int(away_raw)
            except Exception:
                continue
    return None, None

def map_api_status_to_local(status: str, start_ts: int) -> str:
    status = (status or "").upper()

    if status in {"FINISHED", "AWARDED"}:
        return "settled"
    if status in {"IN_PLAY", "PAUSED", "LIVE", "SUSPENDED"}:
        return "closed"
    if status in {"SCHEDULED", "TIMED", "POSTPONED"}:
        return "open"
    if status == "CANCELLED":
        return "closed"
    return "open"


def fetch_football_data_matches_for_competition(competition_code: str, date_from: str, date_to: str) -> list[dict]:
    if not FOOTBALL_DATA_API_KEY:
        return []

    data = fetch_remote_json(
        f"https://api.football-data.org/v4/competitions/{competition_code}/matches?dateFrom={date_from}&dateTo={date_to}",
        {"X-Auth-Token": FOOTBALL_DATA_API_KEY}
    )
    return data.get("matches", [])


def create_auto_betting_match(
    guild_id: int,
    external_id: str,
    home_team: str,
    away_team: str,
    start_ts: int,
    competition_code: str,
    competition_name: str,
) -> int:
    odds_home, odds_draw, odds_away = derive_realistic_odds(home_team, away_team, competition_code)
    conn = db_connect()
    cur = conn.cursor()
    now_ts = int(time.time())

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO betting_matches (
                guild_id, home_team, away_team, start_ts,
                odds_home, odds_draw, odds_away,
                status, result, created_by, created_at,
                source, external_id, auto_created, competition_code, competition_name,
                home_score, away_score, live_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING match_id
        """, (
            guild_id, home_team, away_team, int(start_ts),
            odds_home, odds_draw, odds_away,
            0, now_ts, "football-data", external_id, 1, competition_code, competition_name, None, None, "SCHEDULED"
        ))
        row = cur.fetchone()
        match_id = int(row["match_id"]) if isinstance(row, dict) else int(row[0])
    else:
        cur.execute("""
            INSERT INTO betting_matches (
                guild_id, home_team, away_team, start_ts,
                odds_home, odds_draw, odds_away,
                status, result, created_by, created_at,
                source, external_id, auto_created, competition_code, competition_name,
                home_score, away_score, live_status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            guild_id, home_team, away_team, int(start_ts),
            odds_home, odds_draw, odds_away,
            0, now_ts, "football-data", external_id, 1, competition_code, competition_name, None, None, "SCHEDULED"
        ))
        match_id = int(cur.lastrowid)

    conn.commit()
    conn.close()
    return match_id


def update_auto_betting_match(
    guild_id: int,
    match_id: int,
    home_team: str,
    away_team: str,
    start_ts: int,
    competition_code: str,
    competition_name: str,
    local_status: str,
    live_status: str,
    home_score,
    away_score,
) -> None:
    odds_home, odds_draw, odds_away = derive_realistic_odds(home_team, away_team, competition_code)

    conn = db_connect()
    cur = conn.cursor()

    cur.execute(sql("""
        SELECT home_score, away_score
        FROM betting_matches
        WHERE guild_id = ? AND match_id = ?
    """), (guild_id, match_id))
    current = fetchone_dict(cur) or {"home_score": None, "away_score": None}

    final_home = int(home_score) if home_score is not None else current.get("home_score")
    final_away = int(away_score) if away_score is not None else current.get("away_score")

    cur.execute(sql("""
        UPDATE betting_matches
        SET home_team = ?,
            away_team = ?,
            start_ts = ?,
            odds_home = ?,
            odds_draw = ?,
            odds_away = ?,
            competition_code = ?,
            competition_name = ?,
            home_score = ?,
            away_score = ?,
            live_status = ?,
            status = CASE WHEN status = 'settled' THEN status ELSE ? END
        WHERE guild_id = ? AND match_id = ?
    """), (
        home_team, away_team, int(start_ts),
        odds_home, odds_draw, odds_away,
        competition_code, competition_name, final_home, final_away, live_status, local_status,
        guild_id, match_id
    ))
    conn.commit()
    conn.close()


def sync_auto_matches_for_guild(guild: discord.Guild) -> tuple[int, int]:
    if not FOOTBALL_DATA_API_KEY or not AUTO_FETCH_MATCHES_ENABLED:
        return (0, 0)

    today = datetime.now(timezone.utc).date()
    date_from = (today - timedelta(days=1)).isoformat()
    date_to = (today + timedelta(days=AUTO_FETCH_LOOKAHEAD_DAYS)).isoformat()

    created = 0
    updated = 0

    for competition_code in FOOTBALL_DATA_COMPETITIONS:
        try:
            matches = fetch_football_data_matches_for_competition(competition_code, date_from, date_to)
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, ValueError):
            continue
        except Exception:
            continue

        for item in matches:
            ext_id = f"fd:{item.get('id')}"
            home = ((item.get("homeTeam") or {}).get("shortName")
                    or (item.get("homeTeam") or {}).get("name")
                    or "Gospodarze")
            away = ((item.get("awayTeam") or {}).get("shortName")
                    or (item.get("awayTeam") or {}).get("name")
                    or "Goście")
            utc_date = item.get("utcDate")
            if not utc_date:
                continue

            try:
                start_dt = datetime.fromisoformat(utc_date.replace("Z", "+00:00"))
                start_ts = int(start_dt.timestamp())
            except Exception:
                continue

            competition_name = ((item.get("competition") or {}).get("name") or competition_code)
            api_status = (item.get("status") or "").upper()
            live_status = api_status or "SCHEDULED"
            local_status = map_api_status_to_local(api_status, start_ts)

            home_score, away_score = extract_api_final_scores(item)

            existing = get_match_by_external_id(guild.id, ext_id)
            if existing is None:
                if local_status == "settled":
                    continue
                create_auto_betting_match(
                    guild.id, ext_id, home, away, start_ts, competition_code, competition_name
                )
                created += 1
                existing = get_match_by_external_id(guild.id, ext_id)
            else:
                update_auto_betting_match(
                    guild.id, int(existing["match_id"]), home, away, start_ts,
                    competition_code, competition_name, local_status, live_status, home_score, away_score
                )
                updated += 1
                existing = get_betting_match(guild.id, int(existing["match_id"]))

            if existing is None:
                continue

            # zamknij po starcie / live
            if local_status == "closed" and existing["status"] == "open":
                try:
                    close_betting_match(guild.id, int(existing["match_id"]))
                    updated += 1
                except Exception:
                    pass

            # rozlicz po zakończeniu
            result_pick = normalize_api_result_to_pick(((item.get("score") or {}).get("winner")))
            if api_status in {"FINISHED", "AWARDED"} and result_pick and existing["status"] != "settled":
                try:
                    update_match_scores_and_status(guild.id, int(existing["match_id"]), home_score, away_score, live_status, "settled")
                    settle_betting_match(guild.id, int(existing["match_id"]), result_pick)
                    updated += 1
                except Exception:
                    pass

    return created, updated


def auto_settle_scored_matches_for_guild(guild_id: int) -> tuple[int, int]:
    now_ts = int(time.time())
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_matches
        WHERE guild_id = ?
          AND status != 'settled'
          AND start_ts <= ?
          AND home_score IS NOT NULL
          AND away_score IS NOT NULL
        ORDER BY start_ts ASC
    """), (guild_id, now_ts - 7200))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()

    settled_count = 0
    total_paid = 0

    for row in rows:
        result = derive_result_from_scores(row.get("home_score"), row.get("away_score"))
        if not result:
            continue
        try:
            winners, paid = settle_betting_match(guild_id, int(row["match_id"]), result)
            settled_count += 1
            total_paid += int(paid)
        except Exception:
            pass

    return settled_count, total_paid


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

def normalize_automod_text(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))

    cleaned = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")

    text = " ".join("".join(cleaned).split())
    return text


def collapse_spaced_letters(text: str) -> str:
    # skleja litery rozbijane spacjami: "j e b a c" -> "jebac"
    tokens = text.split()
    result = []
    buffer = []

    for token in tokens:
        if len(token) == 1 and token.isalpha():
            buffer.append(token)
        else:
            if len(buffer) >= 2:
                result.append("".join(buffer))
            elif buffer:
                result.extend(buffer)
            buffer = []
            result.append(token)

    if len(buffer) >= 2:
        result.append("".join(buffer))
    elif buffer:
        result.extend(buffer)

    return " ".join(result)


def is_moderated_channel(channel: discord.abc.GuildChannel) -> bool:
    if getattr(channel, "id", None) in AUTOMOD_EXCLUDED_CHANNEL_IDS:
        return False

    name = normalize_automod_text(getattr(channel, "name", ""))
    return any(keyword in name for keyword in AUTOMOD_CHANNEL_NAME_KEYWORDS)


def detect_automod_violation(content: str):
    normalized = normalize_automod_text(content)
    collapsed = collapse_spaced_letters(normalized)
    compact = collapsed.replace(" ", "")
    variants = [normalized, collapsed, compact]

    for text_variant in variants:
        for pattern in AUTOMOD_BAD_PATTERNS:
            if re.search(pattern, text_variant, flags=re.IGNORECASE):
                return "przekleństwa / wyzwiska"

        for pattern in AUTOMOD_THREAT_PATTERNS:
            if re.search(pattern, text_variant, flags=re.IGNORECASE):
                return "groźby"

        for pattern in AUTOMOD_INSULT_PATTERNS:
            if re.search(pattern, text_variant, flags=re.IGNORECASE):
                if any(x in text_variant for x in ["matk", "stara", "stary", "rodzin"]):
                    return "obrażanie rodziców / rodziny"
                return "obrażanie"

        if any(bad in text_variant for bad in ["cwel", "pedal", "pedał", "morda", "walonywdupe", "walonywdupa", "walonywdupie"]):
            return "obrażanie"

    return None


def contains_discord_invite(content: str) -> bool:
    text = content.lower()
    return (
        "discord.gg/" in text
        or "discord.com/invite/" in text
        or "discordapp.com/invite/" in text
    )


def contains_blocked_external_link(content: str) -> bool:
    text = content.lower()
    if "http://" not in text and "https://" not in text and "www." not in text:
        return False
    return any(keyword in text for keyword in AUTOMOD_BLOCKED_LINK_KEYWORDS)


def contains_shortened_link(content: str) -> bool:
    text = content.lower()
    if "http://" not in text and "https://" not in text and "www." not in text:
        return False
    return any(keyword in text for keyword in AUTOMOD_SHORTENER_KEYWORDS)


def is_exact_score_pick(pick: str) -> bool:
    return str(pick).startswith("SCORE:")


def parse_exact_score_pick(pick: str) -> tuple[int, int]:
    raw = str(pick).split(":", 1)[1]
    home_s, away_s = raw.split("-", 1)
    return int(home_s), int(away_s)


def format_pick_label(pick: str) -> str:
    if is_exact_score_pick(pick):
        home_g, away_g = parse_exact_score_pick(pick)
        return f"dokładny wynik {home_g}:{away_g}"
    return str(pick)


def get_exact_score_odds(match_row: dict, home_goals: int, away_goals: int) -> float:
    # Prosty model kursu dla dokładnego wyniku oparty o 1X2
    if home_goals < 0 or away_goals < 0:
        raise ValueError("Liczba goli nie może być ujemna.")

    total_goals = home_goals + away_goals

    if home_goals > away_goals:
        base = float(match_row["odds_home"])
    elif home_goals == away_goals:
        base = float(match_row["odds_draw"])
    else:
        base = float(match_row["odds_away"])

    multiplier = 2.0 + (total_goals * 0.35)
    if home_goals == away_goals:
        multiplier += 0.45
    if home_goals == 0 or away_goals == 0:
        multiplier += 0.25
    if home_goals >= 4 or away_goals >= 4:
        multiplier += 0.50

    return round(min(60.0, max(3.5, base * multiplier)), 2)


def get_bet_odds_for_pick(match_row: dict, pick: str) -> float:
    if pick == "1":
        return float(match_row["odds_home"])
    if pick.upper() == "X":
        return float(match_row["odds_draw"])
    if pick == "2":
        return float(match_row["odds_away"])
    if is_exact_score_pick(pick):
        home_g, away_g = parse_exact_score_pick(pick)
        return get_exact_score_odds(match_row, home_g, away_g)
    raise ValueError("Niepoprawny typ zakładu.")


def create_betting_match(
    guild_id: int,
    home_team: str,
    away_team: str,
    start_ts: int,
    odds_home: float,
    odds_draw: float,
    odds_away: float,
    created_by: int,
) -> int:
    conn = db_connect()
    cur = conn.cursor()
    now_ts = int(time.time())

    if USING_POSTGRES:
        cur.execute("""
            INSERT INTO betting_matches (
                guild_id, home_team, away_team, start_ts,
                odds_home, odds_draw, odds_away,
                status, result, created_by, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'open', NULL, %s, %s)
            RETURNING match_id
        """, (guild_id, home_team, away_team, int(start_ts), float(odds_home), float(odds_draw), float(odds_away), created_by, now_ts))
        row = cur.fetchone()
        if row is None:
            conn.rollback()
            conn.close()
            raise RuntimeError("Nie udało się utworzyć meczu.")
        if isinstance(row, dict):
            match_id = int(row["match_id"])
        else:
            try:
                match_id = int(row["match_id"])
            except Exception:
                match_id = int(row[0])
    else:
        cur.execute("""
            INSERT INTO betting_matches (
                guild_id, home_team, away_team, start_ts,
                odds_home, odds_draw, odds_away,
                status, result, created_by, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'open', NULL, ?, ?)
        """, (guild_id, home_team, away_team, int(start_ts), float(odds_home), float(odds_draw), float(odds_away), created_by, now_ts))
        match_id = int(cur.lastrowid)

    conn.commit()
    conn.close()
    return match_id


def get_betting_match(guild_id: int, match_id: int) -> dict | None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_matches
        WHERE guild_id = ? AND match_id = ?
    """), (guild_id, match_id))
    row = fetchone_dict(cur)
    conn.close()
    return row


def list_betting_matches(guild_id: int, *, status: str | None = None, limit: int = 20) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    if status is None:
        cur.execute(sql("""
            SELECT *
            FROM betting_matches
            WHERE guild_id = ?
            ORDER BY status ASC, start_ts ASC
            LIMIT ?
        """), (guild_id, limit))
    else:
        cur.execute(sql("""
            SELECT *
            FROM betting_matches
            WHERE guild_id = ? AND status = ?
            ORDER BY start_ts ASC
            LIMIT ?
        """), (guild_id, status, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def place_bet(guild_id: int, match_id: int, user_id: int, pick: str, stake: int, potential_win: int) -> bool:
    conn = db_connect()
    cur = conn.cursor()
    now_ts = int(time.time())

    try:
        if USING_POSTGRES:
            cur.execute("""
                INSERT INTO betting_bets (guild_id, match_id, user_id, pick, stake, potential_win, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (guild_id, match_id, user_id) DO NOTHING
            """, (guild_id, match_id, user_id, pick, int(stake), int(potential_win), now_ts))
            inserted = cur.rowcount > 0
        else:
            cur.execute("""
                INSERT OR IGNORE INTO betting_bets (guild_id, match_id, user_id, pick, stake, potential_win, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, match_id, user_id, pick, int(stake), int(potential_win), now_ts))
            inserted = cur.rowcount > 0

        conn.commit()
    finally:
        conn.close()

    if inserted:
        match_row = get_betting_match(guild_id, match_id)
        odds = get_bet_odds_for_pick(match_row, pick) if match_row else 0.0
        register_bet_placed(guild_id, user_id, int(stake), float(odds))
    return inserted


def get_user_bet(guild_id: int, match_id: int, user_id: int) -> dict | None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT *
        FROM betting_bets
        WHERE guild_id = ? AND match_id = ? AND user_id = ?
    """), (guild_id, match_id, user_id))
    row = fetchone_dict(cur)
    conn.close()
    return row


def list_user_bets(guild_id: int, user_id: int, limit: int = 20) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT b.*, m.home_team, m.away_team, m.status, m.result, m.start_ts
        FROM betting_bets b
        JOIN betting_matches m
          ON b.guild_id = m.guild_id AND b.match_id = m.match_id
        WHERE b.guild_id = ? AND b.user_id = ?
        ORDER BY m.start_ts DESC
        LIMIT ?
    """), (guild_id, user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def close_betting_match(guild_id: int, match_id: int) -> bool:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE betting_matches
        SET status = 'closed'
        WHERE guild_id = ? AND match_id = ? AND status = 'open'
    """), (guild_id, match_id))
    changed = cur.rowcount > 0
    conn.commit()
    conn.close()
    return changed


def settle_betting_match(guild_id: int, match_id: int, result: str) -> tuple[int, int]:
    conn = db_connect()
    cur = conn.cursor()

    cur.execute(sql("""
        SELECT *
        FROM betting_matches
        WHERE guild_id = ? AND match_id = ?
    """), (guild_id, match_id))
    match_row = fetchone_dict(cur)
    if not match_row:
        conn.close()
        raise ValueError("Nie znaleziono meczu.")

    if match_row["status"] == "settled":
        conn.close()
        raise ValueError("Ten mecz jest już rozliczony.")

    cur.execute(sql("""
        SELECT *
        FROM betting_bets
        WHERE guild_id = ? AND match_id = ?
    """), (guild_id, match_id))
    bets = [dict(row) for row in cur.fetchall()]

    winners = 0
    total_paid = 0
    actual_home = int(match_row.get("home_score") or 0)
    actual_away = int(match_row.get("away_score") or 0)

    for bet in bets:
        won = False

        if is_exact_score_pick(bet["pick"]):
            try:
                pick_home, pick_away = parse_exact_score_pick(bet["pick"])
                won = (pick_home == actual_home and pick_away == actual_away)
            except Exception:
                won = False
        else:
            won = (bet["pick"] == result)

        if won:
            payout = int(bet["potential_win"])
            add_points(guild_id, int(bet["user_id"]), payout)
            register_bet_settlement(guild_id, int(bet["user_id"]), won=True, payout=payout)
            winners += 1
            total_paid += payout
        else:
            register_bet_settlement(guild_id, int(bet["user_id"]), won=False, payout=0)

    cur.execute(sql("""
        UPDATE betting_matches
        SET status = 'settled', result = ?
        WHERE guild_id = ? AND match_id = ?
    """), (result, guild_id, match_id))

    conn.commit()
    conn.close()
    return winners, total_paid


def betting_match_embed(match_row: dict) -> discord.Embed:
    status_map = {
        "open": "🟢 Otwarte",
        "closed": "🟡 Zamknięte",
        "settled": "🔴 Rozliczone",
    }
    color = discord.Color.green() if match_row["status"] == "open" else discord.Color.orange()
    if match_row["status"] == "settled":
        color = discord.Color.red()

    embed = discord.Embed(
        title=f"⚽ Mecz #{match_row['match_id']}",
        description=f"**{match_row['home_team']}** vs **{match_row['away_team']}**",
        color=color
    )
    embed.add_field(name="Liga", value=str(match_row.get("competition_name") or match_row.get("competition_code") or "Ręczny mecz"), inline=False)
    embed.add_field(name="Start", value=f"<t:{int(match_row['start_ts'])}:F>", inline=False)
    embed.add_field(
        name="Kursy",
        value=f"1 = {float(match_row['odds_home']):.2f}\nX = {float(match_row['odds_draw']):.2f}\n2 = {float(match_row['odds_away']):.2f}",
        inline=False
    )
    live_status = str(match_row.get("live_status") or "")
    if live_status in {"TIMED", "SCHEDULED", "POSTPONED"} and match_row["status"] == "open":
        score_txt = "brak"
    else:
        live_status = str(match_row.get("live_status") or "")
    if live_status in {"TIMED", "SCHEDULED", "POSTPONED"} and match_row["status"] == "open":
        score_txt = "brak"
    else:
        score_txt = f"{int(match_row.get('home_score') or 0)} : {int(match_row.get('away_score') or 0)}"
    embed.add_field(name="Wynik", value=score_txt, inline=True)
    embed.add_field(name="Status", value=status_map.get(match_row["status"], str(match_row["status"])), inline=True)
    embed.add_field(name="Live", value=str(match_row.get("live_status") or "brak"), inline=True)
    if match_row.get("result"):
        embed.add_field(name="Rozliczono jako", value=str(match_row["result"]), inline=False)
    return embed


def betting_list_embed(rows: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="⚽ Lista meczów", color=discord.Color.blurple())
    if not rows:
        embed.description = "Brak meczów do pokazania."
        return embed

    lines = []
    for row in rows[:10]:
        lines.append(
            f"**#{row['match_id']}** | {row['home_team']} vs {row['away_team']} | "
            f"<t:{int(row['start_ts'])}:R> | **{row['status']}**"
        )
    embed.description = "\n".join(lines)
    return embed


def my_bets_embed(rows: list[dict]) -> discord.Embed:
    embed = discord.Embed(title="🎯 Twoje typy", color=discord.Color.gold())
    if not rows:
        embed.description = "Nie masz jeszcze żadnych typów."
        return embed

    lines = []
    for row in rows[:10]:
        result_txt = f" | wynik: {row['result']}" if row.get("result") else ""
        lines.append(
            f"**#{row['match_id']}** | {row['home_team']} vs {row['away_team']} | "
            f"typ: **{format_pick_label(row['pick'])}** | stawka: **{row['stake']} pkt** | "
            f"wygrana: **{row['potential_win']} pkt** | status: **{row['status']}**{result_txt}"
        )
    embed.description = "\n".join(lines)
    return embed


def betting_panel_embed(guild: discord.Guild) -> discord.Embed:
    rows = list_betting_matches(guild.id, status="open", limit=10)
    embed = discord.Embed(
        title="🤑 Obstawianie meczy",
        description="Kliknij przyciski lub wybierz mecz z listy poniżej.",
        color=discord.Color.green(),
    )
    embed.add_field(name="Minimalna stawka", value=f"{BETTING_MIN_STAKE} pkt", inline=True)
    panel_channel_id = get_betting_panel_channel_id(guild.id) or BETTING_CHANNEL_ID
    embed.add_field(name="Kanał", value=f"<#{panel_channel_id}>", inline=True)

    if not rows:
        embed.add_field(name="Otwarte mecze", value="Aktualnie brak otwartych meczów do obstawiania.", inline=False)
        return embed

    lines = []
    for row in rows[:10]:
        lines.append(
            f"**#{row['match_id']}** | {row['home_team']} vs {row['away_team']}\n"
            f"Liga: **{row.get('competition_name') or row.get('competition_code') or 'Ręczny mecz'}** | Start: <t:{int(row['start_ts'])}:R>\n"
            f"Kursy: **1 {float(row['odds_home']):.2f} / X {float(row['odds_draw']):.2f} / 2 {float(row['odds_away']):.2f}**"
        )

    chunks = []
    current = ""
    for line in lines:
        block = line if not current else "\n\n" + line
        if len(current) + len(block) > 1000:
            if current:
                chunks.append(current)
            current = line
        else:
            current += block
    if current:
        chunks.append(current)

    for idx, chunk in enumerate(chunks, start=1):
        field_name = "Otwarte mecze" if idx == 1 else f"Otwarte mecze {idx}"
        embed.add_field(name=field_name, value=chunk, inline=False)

    embed.set_footer(text="Bot sam tworzy kanały obstawiania i aktualizuje panel automatycznie.")
    return embed


def get_typer_rank_name(total_bets: int, hit_rate: float, roi: float) -> str:
    if total_bets >= 50 and hit_rate >= 60 and roi >= 15:
        return "👑 Legenda Typerów"
    if total_bets >= 30 and hit_rate >= 55 and roi >= 8:
        return "🥇 Elita"
    if total_bets >= 15 and hit_rate >= 50 and roi >= 0:
        return "🥈 Pro Typer"
    if total_bets >= 5:
        return "🥉 Początkujący"
    return "🎯 Debiutant"


def get_recent_betting_history(guild_id: int, user_id: int, limit: int = 10) -> list[dict]:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        SELECT b.*, m.home_team, m.away_team, m.status, m.result, m.start_ts, m.home_score, m.away_score
        FROM betting_bets b
        JOIN betting_matches m
          ON b.guild_id = m.guild_id AND b.match_id = m.match_id
        WHERE b.guild_id = ? AND b.user_id = ?
        ORDER BY b.created_at DESC
        LIMIT ?
    """), (guild_id, user_id, limit))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def recent_history_lines(guild_id: int, user_id: int, limit: int = 5) -> str:
    rows = get_recent_betting_history(guild_id, user_id, limit)
    if not rows:
        return "Brak historii kuponów."

    out_lines = []
    for row in rows:
        status = str(row["status"])
        score_txt = ""
        if status == "settled":
            score_txt = f" | wynik {int(row.get('home_score') or 0)}:{int(row.get('away_score') or 0)}"
        out_lines.append(
            f"**#{row['match_id']}** {row['home_team']} vs {row['away_team']} | "
            f"{format_pick_label(row['pick'])} | {row['stake']} pkt | {status}{score_txt}"
        )
    return "\n".join(out_lines)

def typer_ranking_embed(guild: discord.Guild) -> discord.Embed:
    rows = get_top_typers(guild.id, 10)
    embed = discord.Embed(title="🏆 Ranking typerów", color=discord.Color.gold())
    if not rows:
        embed.description = "Brak statystyk typerów."
        return embed

    lines = []
    pos = 1
    for row in rows:
        member = guild.get_member(int(row["user_id"]))
        if member is None or member.bot:
            continue

        total_bets = int(row["total_bets"])
        wins = int(row["wins"])
        losses = int(row["losses"])
        total_staked = int(row["total_staked"])
        total_won = int(row["total_won"])
        hit_rate = (wins / total_bets * 100.0) if total_bets > 0 else 0.0
        roi = (((total_won - total_staked) / total_staked) * 100.0) if total_staked > 0 else 0.0

        lines.append(
            f"**{pos}. {member.display_name}**\n"
            f"Zakłady: **{total_bets}** | Winrate: **{hit_rate:.1f}%** | ROI: **{roi:.1f}%**\n"
            f"Wygrane: **{wins}** | Przegrane: **{losses}** | Seria: **{int(row['best_streak'])}**"
        )
        pos += 1

    desc = "\n\n".join(lines) if lines else "Brak statystyk typerów."
    embed.description = desc[:4000]
    return embed


def user_typer_stats_embed(guild: discord.Guild, user_id: int) -> discord.Embed:
    row = get_typer_stats_row(guild.id, user_id)
    member = guild.get_member(user_id)
    name = member.display_name if member else str(user_id)

    embed = discord.Embed(title=f"📊 Staty typera PRO: {name}", color=discord.Color.blurple())
    if not row:
        embed.description = "Brak statystyk."
        return embed

    total_bets = int(row["total_bets"])
    wins = int(row["wins"])
    losses = int(row["losses"])
    total_staked = int(row["total_staked"])
    total_won = int(row["total_won"])
    biggest_win = int(row.get("biggest_win") or 0)
    best_odds = float(row.get("best_odds") or 0)
    hit_rate = (wins / total_bets * 100.0) if total_bets > 0 else 0.0
    roi = (((total_won - total_staked) / total_staked) * 100.0) if total_staked > 0 else 0.0
    rank_name = get_typer_rank_name(total_bets, hit_rate, roi)

    embed.add_field(name="Ranga", value=rank_name, inline=False)
    embed.add_field(name="Zakłady", value=str(total_bets), inline=True)
    embed.add_field(name="Wygrane", value=str(wins), inline=True)
    embed.add_field(name="Przegrane", value=str(losses), inline=True)
    embed.add_field(name="Winrate", value=f"{hit_rate:.1f}%", inline=True)
    embed.add_field(name="ROI", value=f"{roi:.1f}%", inline=True)
    embed.add_field(name="Postawione", value=f"{total_staked} pkt", inline=True)
    embed.add_field(name="Wygrane pkt", value=f"{total_won} pkt", inline=True)
    embed.add_field(name="Największa wygrana", value=f"{biggest_win} pkt", inline=True)
    embed.add_field(name="Najlepszy kurs", value=f"{best_odds:.2f}" if best_odds > 0 else "brak", inline=True)
    embed.add_field(name="Aktualna seria", value=str(int(row["current_streak"])), inline=True)
    embed.add_field(name="Najlepsza seria", value=str(int(row["best_streak"])), inline=True)
    embed.add_field(name="Ostatnie kupony", value=recent_history_lines(guild.id, user_id, 5), inline=False)
    return embed

def betting_stats_panel_embed(guild: discord.Guild) -> discord.Embed:
    top_rows = get_top_typers(guild.id, 3)
    embed = discord.Embed(
        title="📊 Profil graczy PRO",
        description="Najważniejsze statystyki typerów, rangi, największe wygrane i szybki dostęp do komend.",
        color=discord.Color.blurple()
    )

    if not top_rows:
        embed.add_field(name="Status", value="Brak statystyk graczy do pokazania.", inline=False)
        return embed

    medals = ["🥇", "🥈", "🥉"]
    lines = []
    for idx, row in enumerate(top_rows):
        member = guild.get_member(int(row["user_id"]))
        if member is None or member.bot:
            continue

        total_bets = int(row["total_bets"])
        wins = int(row["wins"])
        total_staked = int(row["total_staked"])
        total_won = int(row["total_won"])
        biggest_win = int(row.get("biggest_win") or 0)
        best_odds = float(row.get("best_odds") or 0)
        hit_rate = (wins / total_bets * 100.0) if total_bets > 0 else 0.0
        roi = (((total_won - total_staked) / total_staked) * 100.0) if total_staked > 0 else 0.0

        lines.append(
            f"{medals[idx]} **{member.display_name}** — {get_typer_rank_name(total_bets, hit_rate, roi)}\n"
            f"Zakłady: **{total_bets}** | Winrate: **{hit_rate:.1f}%** | ROI: **{roi:.1f}%**\n"
            f"Największa wygrana: **{biggest_win} pkt** | Najlepszy kurs: **{best_odds:.2f}**"
        )

    embed.add_field(name="Top 3 typerów", value="\n\n".join(lines) if lines else "Brak danych.", inline=False)
    embed.add_field(name="Komendy", value="`/moje_staty_typerskie` • `/profil_typera` • `/ranking_typerow` • `/moje_typy`", inline=False)
    return embed

def betting_ranking_panel_embed(guild: discord.Guild) -> discord.Embed:
    rows = get_top_typers(guild.id, 10)
    embed = discord.Embed(
        title="🥇 Ranking typerów",
        description="Najlepsi typerzy na serwerze według wygranych punktów, skuteczności, ROI i serii.",
        color=discord.Color.gold()
    )

    if not rows:
        embed.description = "Brak statystyk typerów."
        return embed

    chunks = []
    current = ""
    pos = 1
    for row in rows:
        member = guild.get_member(int(row["user_id"]))
        if member is None or member.bot:
            continue

        total_bets = int(row["total_bets"])
        wins = int(row["wins"])
        total_staked = int(row["total_staked"])
        total_won = int(row["total_won"])
        biggest_win = int(row.get("biggest_win") or 0)
        best_odds = float(row.get("best_odds") or 0)
        hit_rate = (wins / total_bets * 100.0) if total_bets > 0 else 0.0
        roi = (((total_won - total_staked) / total_staked) * 100.0) if total_staked > 0 else 0.0
        rank_name = get_typer_rank_name(total_bets, hit_rate, roi)

        line = (
            f"**{pos}. {member.display_name}** — {rank_name}\n"
            f"Zakłady: **{total_bets}** | Winrate: **{hit_rate:.1f}%** | ROI: **{roi:.1f}%**\n"
            f"Wygrane pkt: **{total_won}** | Największa wygrana: **{biggest_win}** | Kurs max: **{best_odds:.2f}** | Seria: **{int(row['best_streak'])}**"
        )

        block = line if not current else "\n\n" + line
        if len(current) + len(block) > 1000:
            if current:
                chunks.append(current)
            current = line
        else:
            current += block
        pos += 1

    if current:
        chunks.append(current)

    for idx, chunk in enumerate(chunks, start=1):
        embed.add_field(name="Ranking" if idx == 1 else f"Ranking {idx}", value=chunk, inline=False)

    return embed

def betting_bets_panel_embed(guild: discord.Guild) -> discord.Embed:
    panel_channel_id = get_betting_panel_channel_id(guild.id)
    embed = discord.Embed(
        title="🧾 Typy i kupony",
        description="Tutaj obstawiasz mecze komendami oraz przeglądasz swoje kupony.",
        color=discord.Color.green()
    )
    if panel_channel_id:
        embed.add_field(name="Panel główny", value=f"Wejdź do <#{panel_channel_id}> aby wybrać mecz i typ.", inline=False)
    embed.add_field(name="Komendy", value="`/obstaw` • `/obstaw_dokladny_wynik` • `/moje_typy` • `/moje_staty_typerskie`", inline=False)
    embed.add_field(name="Minimalna stawka", value=f"{BETTING_MIN_STAKE} pkt", inline=False)
    embed.add_field(name="Punkty", value="Wybierasz mecz i typ. Stawka schodzi przy obstawieniu. Za poprawny typ bot przydziela wygraną liczbę punktów, za zły typ stawka przepada.", inline=False)
    return embed


def live_results_embed(guild: discord.Guild) -> discord.Embed:
    rows = list_betting_matches(guild.id, status=None, limit=30)
    embed = discord.Embed(title="🔴 Live wyniki meczów", color=discord.Color.red())

    live_rows = []
    finished_rows = []
    now_ts = int(time.time())

    for row in rows:
        live_status = str(row.get("live_status") or "")
        if row["status"] == "closed" or live_status in {"IN_PLAY", "PAUSED"}:
            live_rows.append(row)
        elif row["status"] == "settled":
            finished_rows.append(row)

    lines = []
    for row in live_rows[:LIVE_RESULTS_LIMIT]:
        live_status = str(row.get("live_status") or "")
        if live_status in {"TIMED", "SCHEDULED", "POSTPONED"} and row["status"] == "open":
            score_part = "vs"
        else:
            score_part = f"{int(row.get('home_score') or 0)}:{int(row.get('away_score') or 0)}"
        lines.append(
            f"**#{row['match_id']}** | {row['home_team']} {score_part} {row['away_team']}\n"
            f"Live: **{row.get('live_status') or row['status']}** | Liga: **{row.get('competition_name') or row.get('competition_code') or 'brak'}**"
        )

    if not lines:
        soon = [r for r in rows if r["status"] == "open" and int(r["start_ts"]) >= now_ts]
        for row in soon[:LIVE_RESULTS_LIMIT]:
            lines.append(
                f"**#{row['match_id']}** | {row['home_team']} vs {row['away_team']}\n"
                f"Start: <t:{int(row['start_ts'])}:R> | Liga: **{row.get('competition_name') or row.get('competition_code') or 'brak'}**"
            )

    if finished_rows:
        last = finished_rows[:3]
        tail = []
        for row in last:
            tail.append(
                f"FT | **{row['home_team']} {int(row.get('home_score') or 0)}:{int(row.get('away_score') or 0)} {row['away_team']}**"
            )
        embed.add_field(name="Ostatnio zakończone", value="\n".join(tail), inline=False)

    desc = "\n\n".join(lines) if lines else "Brak aktywnych lub nadchodzących meczów."
    embed.description = desc[:4000]
    return embed


class BetStakeModal(discord.ui.Modal, title="🎯 Postaw zakład"):
    stake = discord.ui.TextInput(label="Stawka w punktach", placeholder="Np. 100", required=True, max_length=10)

    def __init__(self, match_id: int, pick: str):
        super().__init__()
        self.match_id = int(match_id)
        self.pick = pick

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        try:
            stake_value = int(str(self.stake).strip())
        except ValueError:
            await safe_interaction_send(interaction, content="❌ Stawka musi być liczbą całkowitą.", ephemeral=True)
            return

        if stake_value < BETTING_MIN_STAKE:
            await safe_interaction_send(interaction, content=f"❌ Minimalna stawka to {BETTING_MIN_STAKE} pkt.", ephemeral=True)
            return

        match_row = get_betting_match(interaction.guild.id, self.match_id)
        if not match_row:
            await safe_interaction_send(interaction, content="❌ Nie znaleziono meczu.", ephemeral=True)
            return

        if match_row["status"] != "open":
            await safe_interaction_send(interaction, content="❌ Ten mecz nie jest już otwarty do obstawiania.", ephemeral=True)
            return

        if int(match_row["start_ts"]) <= int(time.time()):
            await safe_interaction_send(interaction, content="❌ Czas obstawiania minął.", ephemeral=True)
            return

        existing_bet = get_user_bet(interaction.guild.id, self.match_id, interaction.user.id)
        if existing_bet:
            await safe_interaction_send(interaction, content="❌ Już obstawiłeś ten mecz.", ephemeral=True)
            return

        points_row = get_points_row(interaction.guild.id, interaction.user.id)
        total_points = int(points_row["total_points"]) if points_row else 0
        if total_points < stake_value:
            await safe_interaction_send(interaction, content="❌ Nie masz tyle punktów.", ephemeral=True)
            return

        odds = get_bet_odds_for_pick(match_row, self.pick)
        potential_win = int(round(stake_value * odds))

        inserted = place_bet(interaction.guild.id, self.match_id, interaction.user.id, self.pick, stake_value, potential_win)
        if not inserted:
            await safe_interaction_send(interaction, content="❌ Nie udało się zapisać zakładu.", ephemeral=True)
            return

        remove_total_points(interaction.guild.id, interaction.user.id, stake_value)
        embed = discord.Embed(title="✅ Zakład przyjęty", color=discord.Color.green())
        embed.add_field(name="Mecz", value=f"#{self.match_id} | {match_row['home_team']} vs {match_row['away_team']}", inline=False)
        embed.add_field(name="Typ", value=self.pick, inline=True)
        embed.add_field(name="Stawka", value=f"{stake_value} pkt", inline=True)
        embed.add_field(name="Możliwa wygrana", value=f"{potential_win} pkt", inline=True)
        await safe_interaction_send(interaction, embed=embed, ephemeral=True)



class ExactScoreBetModal(discord.ui.Modal, title="🎯 Dokładny wynik"):
    home_goals = discord.ui.TextInput(label="Gole gospodarzy", placeholder="Np. 2", required=True, max_length=2)
    away_goals = discord.ui.TextInput(label="Gole gości", placeholder="Np. 1", required=True, max_length=2)
    stake = discord.ui.TextInput(label="Stawka w punktach", placeholder="Np. 100", required=True, max_length=10)

    def __init__(self, match_id: int):
        super().__init__()
        self.match_id = int(match_id)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        try:
            home_g = int(str(self.home_goals).strip())
            away_g = int(str(self.away_goals).strip())
            stake_value = int(str(self.stake).strip())
        except ValueError:
            await safe_interaction_send(interaction, content="❌ Musisz wpisać liczby całkowite.", ephemeral=True)
            return

        if home_g < 0 or away_g < 0:
            await safe_interaction_send(interaction, content="❌ Liczba goli nie może być ujemna.", ephemeral=True)
            return

        if stake_value < BETTING_MIN_STAKE:
            await safe_interaction_send(interaction, content=f"❌ Minimalna stawka to {BETTING_MIN_STAKE} pkt.", ephemeral=True)
            return

        match_row = get_betting_match(interaction.guild.id, self.match_id)
        if not match_row:
            await safe_interaction_send(interaction, content="❌ Nie znaleziono meczu.", ephemeral=True)
            return

        if match_row["status"] != "open":
            await safe_interaction_send(interaction, content="❌ Ten mecz nie jest już otwarty do obstawiania.", ephemeral=True)
            return

        if int(match_row["start_ts"]) <= int(time.time()):
            await safe_interaction_send(interaction, content="❌ Czas obstawiania minął.", ephemeral=True)
            return

        existing_bet = get_user_bet(interaction.guild.id, self.match_id, interaction.user.id)
        if existing_bet:
            await safe_interaction_send(interaction, content="❌ Już obstawiłeś ten mecz.", ephemeral=True)
            return

        points_row = get_points_row(interaction.guild.id, interaction.user.id)
        total_points = int(points_row["total_points"]) if points_row else 0
        if total_points < stake_value:
            await safe_interaction_send(interaction, content="❌ Nie masz tyle punktów.", ephemeral=True)
            return

        pick = f"SCORE:{home_g}-{away_g}"
        odds = get_bet_odds_for_pick(match_row, pick)
        potential_win = int(round(stake_value * odds))

        inserted = place_bet(interaction.guild.id, self.match_id, interaction.user.id, pick, stake_value, potential_win)
        if not inserted:
            await safe_interaction_send(interaction, content="❌ Nie udało się zapisać zakładu.", ephemeral=True)
            return

        remove_total_points(interaction.guild.id, interaction.user.id, stake_value)

        embed = discord.Embed(title="✅ Zakład na dokładny wynik przyjęty", color=discord.Color.green())
        embed.add_field(name="Mecz", value=f"#{self.match_id} | {match_row['home_team']} vs {match_row['away_team']}", inline=False)
        embed.add_field(name="Typ", value=f"{home_g}:{away_g}", inline=True)
        embed.add_field(name="Kurs", value=f"{odds:.2f}", inline=True)
        embed.add_field(name="Stawka", value=f"{stake_value} pkt", inline=True)
        embed.add_field(name="Możliwa wygrana", value=f"{potential_win} pkt", inline=False)
        await safe_interaction_send(interaction, embed=embed, ephemeral=True)


class BettingPickView(discord.ui.View):
    def __init__(self, match_id: int):
        super().__init__(timeout=180)
        self.match_id = int(match_id)

    @discord.ui.button(label="1", style=discord.ButtonStyle.success, row=0)
    async def pick_home(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetStakeModal(self.match_id, "1"))

    @discord.ui.button(label="X", style=discord.ButtonStyle.secondary, row=0)
    async def pick_draw(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetStakeModal(self.match_id, "X"))

    @discord.ui.button(label="2", style=discord.ButtonStyle.danger, row=0)
    async def pick_away(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(BetStakeModal(self.match_id, "2"))

    @discord.ui.button(label="🎯 Dokładny wynik", style=discord.ButtonStyle.primary, row=1)
    async def exact_score(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ExactScoreBetModal(self.match_id))


class BettingMatchSelect(discord.ui.Select):
    def __init__(self, guild_id: int):
        rows = list_betting_matches(guild_id, status="open", limit=25)
        options = []

        if rows:
            for row in rows[:25]:
                label = f"#{row['match_id']} {row['home_team']} vs {row['away_team']}"
                description = f"{(row.get('competition_code') or 'LIGA')} | 1:{float(row['odds_home']):.2f} X:{float(row['odds_draw']):.2f} 2:{float(row['odds_away']):.2f}"
                options.append(discord.SelectOption(label=label[:100], description=description[:100], value=str(row['match_id'])))

        if not options:
            options.append(discord.SelectOption(label="Brak otwartych meczów", value="none"))

        super().__init__(
            placeholder="Wybierz mecz do obstawienia",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"betting_match_select_{guild_id}",
            disabled=(len(rows) == 0),
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "none":
            await safe_interaction_send(interaction, content="❌ Aktualnie brak otwartych meczów.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        match_id = int(self.values[0])
        match_row = get_betting_match(interaction.guild.id, match_id)
        if not match_row:
            await interaction.followup.send("❌ Nie znaleziono meczu.", ephemeral=True)
            return

        embed = betting_match_embed(match_row)
        embed.add_field(name="Jak obstawić", value="Kliknij 1, X, 2 albo **Dokładny wynik** i podaj stawkę w punktach.", inline=False)
        await interaction.followup.send(embed=embed, view=BettingPickView(match_id), ephemeral=True)


class BettingPanelView(discord.ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=None)
        self.add_item(BettingMatchSelect(guild_id))

    @discord.ui.button(label="🔄 Odśwież", style=discord.ButtonStyle.primary, row=1, custom_id="betting_refresh")
    async def refresh_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await refresh_betting_panel(interaction.guild, force=True)
        await refresh_live_results_panel(interaction.guild, force=True)
        await refresh_betting_side_panels(interaction.guild, force=True)
        await interaction.followup.send("✅ Panele obstawiania zostały odświeżone.", ephemeral=True)

    @discord.ui.button(label="🎯 Moje typy", style=discord.ButtonStyle.secondary, row=1, custom_id="betting_my_bets")
    async def my_bets_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        rows = list_user_bets(interaction.guild.id, interaction.user.id, limit=20)
        await interaction.followup.send(embed=my_bets_embed(rows), ephemeral=True)

    @discord.ui.button(label="🏆 Ranking typerów", style=discord.ButtonStyle.secondary, row=1, custom_id="betting_typer_ranking")
    async def typer_ranking_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=typer_ranking_embed(interaction.guild), ephemeral=True)

    @discord.ui.button(label="🔴 Live", style=discord.ButtonStyle.danger, row=1, custom_id="betting_live")
    async def live_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        await refresh_live_results_panel(interaction.guild, force=True)
        await interaction.followup.send(embed=live_results_embed(interaction.guild), ephemeral=True)


async def refresh_betting_panel(guild: discord.Guild, *, force: bool = False) -> None:
    now_ts = time.time()
    cache_key = (guild.id, "betting")
    last_ts = bot.panel_refresh_cache.get(cache_key, 0.0)

    if not force and now_ts - last_ts < BETTING_PANEL_REFRESH_SECONDS:
        return

    await ensure_panel_message(guild, "betting", betting_panel_embed(guild), BettingPanelView(guild.id))
    bot.panel_refresh_cache[cache_key] = now_ts


async def refresh_live_results_panel(guild: discord.Guild, *, force: bool = False) -> None:
    now_ts = time.time()
    cache_key = (guild.id, "betting_live")
    last_ts = bot.panel_refresh_cache.get(cache_key, 0.0)

    if not force and now_ts - last_ts < BETTING_LIVE_REFRESH_SECONDS:
        return

    await ensure_panel_message(guild, "betting_live", live_results_embed(guild), None)
    bot.panel_refresh_cache[cache_key] = now_ts



async def refresh_betting_side_panels(guild: discord.Guild, *, force: bool = False) -> None:
    await ensure_panel_message(guild, "betting_bets", betting_bets_panel_embed(guild), None)
    await ensure_panel_message(guild, "betting_ranking", betting_ranking_panel_embed(guild), None)
    await ensure_panel_message(guild, "betting_stats", betting_stats_panel_embed(guild), None)


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
        self.panel_refresh_cache: dict[tuple[int, str], float] = {}
        self.betting_system_channels: dict[int, dict[str, int]] = {}

    async def setup_hook(self) -> None:
        self.add_view(ShopView(self))
        self.add_view(PointsView(self))
        self.add_view(RankingView(self))
        self.add_view(XpInfoView(self))
        self.add_view(ChatModerationPanelView())
        # widok obstawiania dla aktywnego serwera odświeża się przez panel

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
    embed.add_field(name="🛡️ System kar", value=f"AutoMod daje warny. 1 = ostrzeżenie, 10 = kick, 20 = ban. Co {AUTOMOD_WARN_DECAY_HOURS}h bez przewinień schodzi 1 warn.", inline=False)
    embed.add_field(name="🔗 Linki", value="Discord invite = natychmiastowy ban. TikTok / YouTube / Kick / skrócone linki = usunięcie + warn.", inline=False)
    embed.add_field(name="⚙️ Panel moderacji", value="Użyj `/panel_moderacji`, `/moderacja_on`, `/moderacja_off`, `/status_moderacji`.", inline=False)
    embed.add_field(name="🎯 Obstawianie", value="Bot sam tworzy kategorię i kanały obstawiania. Użyj `/panel_obstawiania`. Dostępny też **dokładny wynik**.", inline=False)
    embed.add_field(name="⚽ Auto mecze", value="Bot może pobierać mecze z football-data.org i sam aktualizować panel. Użyj `/sync_mecze_auto`.", inline=False)
    embed.add_field(name="🏆 Typerzy i LIVE", value="Masz `/ranking_typerow`, `/moje_staty_typerskie`, `/profil_typera` i panel LIVE wyników.", inline=False)
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


def get_runtime_panel_channel_id(guild_id: int, panel_key: str) -> int | None:
    if panel_key in {"betting", "betting_live", "betting_bets", "betting_ranking", "betting_stats"}:
        channel_map = bot.betting_system_channels.get(guild_id, {})
        return channel_map.get(panel_key)
    return PANEL_CHANNELS.get(panel_key)


def get_betting_panel_channel_id(guild_id: int) -> int | None:
    channel_map = bot.betting_system_channels.get(guild_id, {})
    return channel_map.get("betting")


def get_betting_live_channel_id(guild_id: int) -> int | None:
    channel_map = bot.betting_system_channels.get(guild_id, {})
    return channel_map.get("betting_live")


def get_betting_bets_channel_id(guild_id: int) -> int | None:
    channel_map = bot.betting_system_channels.get(guild_id, {})
    return channel_map.get("betting_bets")


async def ensure_betting_system_channels(guild: discord.Guild) -> dict[str, int]:
    category = discord.utils.get(guild.categories, name=BETTING_CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(BETTING_CATEGORY_NAME)

    created: dict[str, int] = {}

    for key, channel_name in BETTING_AUTO_CHANNELS.items():
        channel = discord.utils.get(guild.text_channels, name=channel_name)
        if channel is None:
            channel = await guild.create_text_channel(
                name=channel_name,
                category=category,
                reason="Automatyczne tworzenie kanałów obstawiania",
            )
        elif channel.category != category:
            try:
                await channel.edit(category=category, reason="Naprawa kategorii systemu obstawiania")
            except discord.HTTPException:
                pass

        created[key] = channel.id

    bot.betting_system_channels[guild.id] = created
    return created


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
    channel_id = get_runtime_panel_channel_id(guild.id, panel_key)
    if channel_id is None:
        return
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
    await ensure_panel_message(guild, "ranking", ranking_embed(guild), RankingView(bot))
    await ensure_panel_message(guild, "xpinfo", xpinfo_embed(), XpInfoView(bot))
    await ensure_panel_message(guild, "shop", shop_embed(), ShopView(bot))
    await ensure_panel_message(guild, "betting", betting_panel_embed(guild), BettingPanelView(guild.id))
    await ensure_panel_message(guild, "betting_live", live_results_embed(guild), None)
    await ensure_panel_message(guild, "betting_bets", betting_bets_panel_embed(guild), None)
    await ensure_panel_message(guild, "betting_ranking", betting_ranking_panel_embed(guild), None)
    await ensure_panel_message(guild, "betting_stats", betting_stats_panel_embed(guild), None)

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

class ChatModerationPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🟢 Włącz moderację", style=discord.ButtonStyle.success, custom_id="chat_mod_enable")
    async def enable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await safe_interaction_send(interaction, content="❌ Nie masz uprawnień do zarządzania serwerem.", ephemeral=True)
            return

        set_chat_moderation_enabled(interaction.guild.id, True)
        embed = discord.Embed(
            title="🛡️ Panel moderacji czata",
            description=f"Status moderacji czata: **{chat_moderation_status_text(interaction.guild.id)}**",
            color=discord.Color.green(),
        )
        embed.add_field(name="Sterowanie", value="Kliknij przycisk, aby włączyć lub wyłączyć moderację czata głównego.", inline=False)
        await interaction.response.edit_message(embed=embed, view=ChatModerationPanelView())

    @discord.ui.button(label="🔴 Wyłącz moderację", style=discord.ButtonStyle.danger, custom_id="chat_mod_disable")
    async def disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.manage_guild:
            await safe_interaction_send(interaction, content="❌ Nie masz uprawnień do zarządzania serwerem.", ephemeral=True)
            return

        set_chat_moderation_enabled(interaction.guild.id, False)
        embed = discord.Embed(
            title="🛡️ Panel moderacji czata",
            description=f"Status moderacji czata: **{chat_moderation_status_text(interaction.guild.id)}**",
            color=discord.Color.red(),
        )
        embed.add_field(name="Sterowanie", value="Kliknij przycisk, aby włączyć lub wyłączyć moderację czata głównego.", inline=False)
        await interaction.response.edit_message(embed=embed, view=ChatModerationPanelView())

    @discord.ui.button(label="📊 Status", style=discord.ButtonStyle.secondary, custom_id="chat_mod_status")
    async def status_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await safe_interaction_send(interaction, content="Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🛡️ Panel moderacji czata",
            description=f"Status moderacji czata: **{chat_moderation_status_text(interaction.guild.id)}**",
            color=discord.Color.blurple(),
        )
        embed.add_field(name="Sterowanie", value="Kliknij przycisk, aby włączyć lub wyłączyć moderację czata głównego.", inline=False)
        await interaction.response.edit_message(embed=embed, view=ChatModerationPanelView())


# =========================================================
# EVENTY
# =========================================================
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot or message.guild is None:
        return

    if not message.content or not message.content.strip():
        return

    if AUTOMOD_ENABLED and is_chat_moderation_enabled(message.guild.id) and isinstance(message.channel, discord.TextChannel):
        if is_moderated_channel(message.channel):
            member = message.guild.get_member(message.author.id)

            # BAN za zaproszenia do innych Discordów
            if AUTOMOD_BAN_DISCORD_INVITES and contains_discord_invite(message.content):
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

                if member is not None:
                    try:
                        await member.ban(reason="AutoMod: reklama innego Discorda", delete_message_days=0)
                        delete_user_data(message.guild.id, member.id)
                    except Exception:
                        pass
                return

            # Blokada TikTok / YouTube / Kick
            if AUTOMOD_BLOCK_EXTERNAL_LINKS and contains_blocked_external_link(message.content):
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

                warn_count = add_automod_warning(message.guild.id, message.author.id, "reklama / link zewnętrzny")
                action_text = ""
                member = message.guild.get_member(message.author.id)

                if member is not None and warn_count >= AUTOMOD_WARN_BAN_AT:
                    try:
                        await member.ban(reason=f"AutoMod hardcore: reklama / link zewnętrzny | warn #{warn_count}", delete_message_days=0)
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **zbanowany**."
                    except Exception:
                        action_text = ""
                elif member is not None and warn_count >= AUTOMOD_WARN_KICK_AT:
                    try:
                        await member.kick(reason=f"AutoMod hardcore: reklama / link zewnętrzny | warn #{warn_count}")
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **wyrzucony z serwera**."
                    except Exception:
                        action_text = ""
                elif warn_count == 1:
                    action_text = " Zachowuj się bo wylecisz."

                if AUTOMOD_DELETE_AND_WARN:
                    try:
                        warning = await message.channel.send(
                            f"⚠️ {message.author.mention}, link został usunięty. Masz teraz **{warn_count} warnów**.{action_text}"
                        )
                        await warning.delete(delay=AUTOMOD_WARNING_DELETE_AFTER)
                    except discord.HTTPException:
                        pass
                return

            # Blokada skrótów linków
            if AUTOMOD_SHORTENER_WARN and contains_shortened_link(message.content):
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

                warn_count = add_automod_warning(message.guild.id, message.author.id, "skrócony link")
                action_text = ""
                member = message.guild.get_member(message.author.id)

                if member is not None and warn_count >= AUTOMOD_WARN_BAN_AT:
                    try:
                        await member.ban(reason=f"AutoMod hardcore: skrócony link | warn #{warn_count}", delete_message_days=0)
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **zbanowany**."
                    except Exception:
                        action_text = ""
                elif member is not None and warn_count >= AUTOMOD_WARN_KICK_AT:
                    try:
                        await member.kick(reason=f"AutoMod hardcore: skrócony link | warn #{warn_count}")
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **wyrzucony z serwera**."
                    except Exception:
                        action_text = ""
                elif warn_count == 1:
                    action_text = " Zachowuj się bo wylecisz."

                if AUTOMOD_DELETE_AND_WARN:
                    try:
                        warning = await message.channel.send(
                            f"⚠️ {message.author.mention}, skrócony link został usunięty. Masz teraz **{warn_count} warnów**.{action_text}"
                        )
                        await warning.delete(delay=AUTOMOD_WARNING_DELETE_AFTER)
                    except discord.HTTPException:
                        pass
                return

            violation = detect_automod_violation(message.content)
            if violation is not None:
                try:
                    await message.delete()
                except discord.HTTPException:
                    pass

                warn_count = add_automod_warning(message.guild.id, message.author.id, violation)

                action_text = ""
                member = message.guild.get_member(message.author.id)

                if member is not None and warn_count >= AUTOMOD_WARN_BAN_AT:
                    try:
                        await member.ban(reason=f"AutoMod hardcore: {violation} | warn #{warn_count}", delete_message_days=0)
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **zbanowany**."
                    except Exception:
                        action_text = ""
                elif member is not None and warn_count >= AUTOMOD_WARN_KICK_AT:
                    try:
                        await member.kick(reason=f"AutoMod hardcore: {violation} | warn #{warn_count}")
                        delete_user_data(message.guild.id, member.id)
                        action_text = " Osiągnięto limit warnów — użytkownik został **wyrzucony z serwera**."
                    except Exception:
                        action_text = ""
                elif warn_count == 1:
                    action_text = " Zachowuj się bo wylecisz."

                if AUTOMOD_DELETE_AND_WARN:
                    try:
                        warning = await message.channel.send(
                            f"⚠️ {message.author.mention}, wiadomość usunięta za: **{violation}**. Masz teraz **{warn_count} warnów**.{action_text}"
                        )
                        await warning.delete(delay=AUTOMOD_WARNING_DELETE_AFTER)
                    except discord.HTTPException:
                        pass

                return

    count = update_message_count(message.guild.id, message.author.id)

    if count % TEXT_MESSAGES_REQUIRED == 0:
        member = message.guild.get_member(message.author.id)
        if member:
            add_points_with_role_bonus(member, text_points=TEXT_POINTS)

    await bot.process_commands(message)


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
async def on_member_update(before: discord.Member, after: discord.Member):
    if not is_real_user(after):
        return

    if before.timed_out_until != after.timed_out_until:
        moderator, reason = await get_recent_audit_actor_and_reason(
            after.guild,
            discord.AuditLogAction.member_update,
            after.id
        )
        is_timeout = after.timed_out_until is not None and (before.timed_out_until != after.timed_out_until)

        if is_timeout:
            reset_user_points(after.guild.id, after.id)

        title = "⏳ Timeout + reset punktów" if is_timeout else "✅ Zdjęto timeout"
        color = discord.Color.orange() if is_timeout else discord.Color.green()
        embed = discord.Embed(title=title, color=color)
        embed.add_field(name="Użytkownik", value=f"{after.mention} ({after.id})", inline=False)

        if moderator and not moderator.bot:
            embed.add_field(name="Kto wyciszył", value=moderator.mention, inline=False)

        if after.timed_out_until:
            embed.add_field(name="Do kiedy", value=f"<t:{int(after.timed_out_until.timestamp())}:F>", inline=False)
            embed.add_field(name="Punkty", value="Wyzerowane", inline=False)

        embed.add_field(name="Powód", value=reason or "brak", inline=False)
        await send_admin_log(after.guild, embed)

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

        try:
            await ensure_betting_system_channels(guild)
        except Exception as e:
            print(f"⚠️ Błąd tworzenia kanałów obstawiania dla {guild.name}: {e}")

        if AUTO_FETCH_MATCHES_ENABLED and FOOTBALL_DATA_API_KEY:
            try:
                created, updated = await asyncio.to_thread(sync_auto_matches_for_guild, guild)
                settled_count, _ = await asyncio.to_thread(auto_settle_scored_matches_for_guild, guild.id)
                print(f"⚽ Auto-sync {guild.name}: dodano {created}, zaktualizowano {updated}, rozliczono {settled_count}")
            except Exception as e:
                print(f"⚠️ Błąd auto-sync dla {guild.name}: {e}")

        await refresh_all_panels(guild)

        admin_log_channel = guild.get_channel(ADMIN_LOG_CHANNEL_ID)
        if admin_log_channel is None:
            print(f"⚠️ Nie znaleziono kanału logów administracyjnych na serwerze {guild.name}: {ADMIN_LOG_CHANNEL_ID}")

    if not vc_loop.is_running():
        vc_loop.start()
    if not betting_panel_loop.is_running():
        betting_panel_loop.start()
    if not auto_fetch_matches_loop.is_running():
        auto_fetch_matches_loop.start()

    try:
        synced = await bot.tree.sync()
        print(f"Zsynchronizowano {len(synced)} komend slash.")
    except Exception as e:
        print(f"Błąd synchronizacji komend: {e}")

# =========================================================
# VC LOOP
# =========================================================
@tasks.loop(minutes=AUTO_FETCH_INTERVAL_MINUTES)
async def auto_fetch_matches_loop():
    if not AUTO_FETCH_MATCHES_ENABLED or not FOOTBALL_DATA_API_KEY:
        return

    for guild in bot.guilds:
        try:
            await asyncio.to_thread(sync_auto_matches_for_guild, guild)
            await asyncio.to_thread(auto_settle_scored_matches_for_guild, guild.id)
            await refresh_betting_panel(guild)
            await refresh_live_results_panel(guild)
            await refresh_betting_side_panels(guild)
            await refresh_betting_side_panels(guild)
        except Exception:
            pass


@auto_fetch_matches_loop.before_loop
async def before_auto_fetch_matches_loop():
    await bot.wait_until_ready()


@tasks.loop(minutes=5)
async def betting_panel_loop():
    for guild in bot.guilds:
        try:
            await refresh_betting_panel(guild)
            await refresh_live_results_panel(guild)
            await refresh_betting_side_panels(guild)
        except Exception:
            pass


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


@bot.tree.command(name="setup_obstawianie_auto", description="Tworzy lub naprawia automatycznie kategorię i kanały obstawiania")
@app_commands.checks.has_permissions(manage_guild=True)
async def setup_obstawianie_auto(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    created = await ensure_betting_system_channels(interaction.guild)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)
    panel_id = created.get("betting")
    live_id = created.get("betting_live")
    bets_id = created.get("betting_bets")
    ranking_id = created.get("betting_ranking")
    stats_id = created.get("betting_stats")

    embed = discord.Embed(title="✅ System obstawiania gotowy", color=discord.Color.green())
    embed.add_field(name="Kategoria", value=BETTING_CATEGORY_NAME, inline=False)
    embed.add_field(
        name="Kanały",
        value=(
            f"Panel: <#{panel_id}>\n"
            f"Live: <#{live_id}>\n"
            f"Typy: <#{bets_id}>\n"
            f"Ranking: <#{ranking_id}>\n"
            f"Staty: <#{stats_id}>"
        ),
        inline=False
    )
    await safe_interaction_send(interaction, embed=embed, ephemeral=True)


@bot.tree.command(name="panel_moderacji", description="Premium panel włączania i wyłączania moderacji czata")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel_moderacji(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🛡️ Panel moderacji czata",
        description=f"Status moderacji czata: **{chat_moderation_status_text(interaction.guild.id)}**",
        color=discord.Color.blurple(),
    )
    embed.add_field(name="Sterowanie", value="Kliknij przycisk poniżej, aby włączyć lub wyłączyć moderację czata głównego.", inline=False)
    await safe_interaction_send(interaction, embed=embed, view=ChatModerationPanelView(), ephemeral=False)


@bot.tree.command(name="moderacja_on", description="Włącza moderację czata")
@app_commands.checks.has_permissions(manage_guild=True)
async def moderacja_on(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    set_chat_moderation_enabled(interaction.guild.id, True)
    await safe_interaction_send(interaction, content="✅ Moderacja czata została włączona.", ephemeral=True)


@bot.tree.command(name="moderacja_off", description="Wyłącza moderację czata")
@app_commands.checks.has_permissions(manage_guild=True)
async def moderacja_off(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    set_chat_moderation_enabled(interaction.guild.id, False)
    await safe_interaction_send(interaction, content="⛔ Moderacja czata została wyłączona.", ephemeral=True)


@bot.tree.command(name="status_moderacji", description="Pokazuje status moderacji czata")
async def status_moderacji(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await safe_interaction_send(
        interaction,
        content=f"🛡️ Moderacja czata jest teraz **{chat_moderation_status_text(interaction.guild.id)}**.",
        ephemeral=True
    )


@bot.tree.command(name="warny", description="Pokazuje liczbę warnów użytkownika")
async def warny(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    count = get_automod_warning_count(interaction.guild.id, interaction.user.id)
    embed = discord.Embed(title="🛡️ Twoje warny", color=discord.Color.orange())
    embed.add_field(name="Liczba warnów", value=str(count), inline=False)
    embed.add_field(name="Kary", value="1 warn = ostrzeżenie\n10 warnów = kick\n20 warnów = ban", inline=False)
    embed.add_field(name="Linki", value="Discord invite = ban\nTikTok / YouTube / Kick / skrócone linki = warn", inline=False)
    embed.add_field(name="Zmniejszanie warnów", value=f"Co {AUTOMOD_WARN_DECAY_HOURS}h bez przewinień schodzi 1 warn.", inline=False)
    await safe_interaction_send(interaction, embed=embed, ephemeral=True)


@bot.tree.command(name="warny_admin", description="Pokazuje warny wybranego użytkownika")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(uzytkownik="Użytkownik do sprawdzenia")
async def warny_admin(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    count = get_automod_warning_count(interaction.guild.id, uzytkownik.id)
    embed = discord.Embed(title="🛡️ Warny użytkownika", color=discord.Color.orange())
    embed.add_field(name="Użytkownik", value=uzytkownik.mention, inline=False)
    embed.add_field(name="Liczba warnów", value=str(count), inline=False)
    embed.add_field(name="Zmniejszanie warnów", value=f"Co {AUTOMOD_WARN_DECAY_HOURS}h bez przewinień schodzi 1 warn.", inline=False)
    embed.add_field(name="Kary", value="1 = ostrzeżenie\n10 = kick\n20 = ban", inline=False)
    await safe_interaction_send(interaction, embed=embed, ephemeral=True)


@bot.tree.command(name="reset_warnow", description="Resetuje warny użytkownika")
@app_commands.checks.has_permissions(manage_messages=True)
@app_commands.describe(uzytkownik="Użytkownik do resetu warnów")
async def reset_warnow(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    clear_automod_warnings(interaction.guild.id, uzytkownik.id)
    await safe_interaction_send(interaction, content=f"✅ Zresetowano warny użytkownika {uzytkownik.mention}.", ephemeral=True)




@bot.tree.command(name="auto_rozlicz_mecze", description="Wymusza auto rozliczenie zakończonych meczów z zapisanym wynikiem")
@app_commands.checks.has_permissions(manage_guild=True)
async def auto_rozlicz_mecze(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)
    settled_count, total_paid = await asyncio.to_thread(auto_settle_scored_matches_for_guild, interaction.guild.id)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)
    await interaction.followup.send(
        f"✅ Auto rozliczenie zakończone. Rozliczono meczów: **{settled_count}**, wypłacono łącznie: **{total_paid} pkt**.",
        ephemeral=True
    )


@bot.tree.command(name="sync_mecze_auto", description="Ręcznie pobiera mecze z API i odświeża panele obstawiania")
@app_commands.checks.has_permissions(manage_guild=True)
async def sync_mecze_auto(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if not FOOTBALL_DATA_API_KEY:
        await safe_interaction_send(interaction, content="❌ Brak FOOTBALL_DATA_API_KEY w Railway / env.", ephemeral=True)
        return

    created, updated = await asyncio.to_thread(sync_auto_matches_for_guild, interaction.guild)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await safe_interaction_send(
        interaction,
        content=f"✅ Synchronizacja zakończona. Dodano: **{created}**, zaktualizowano / zamknięto / rozliczono: **{updated}**.",
        ephemeral=True
    )


@bot.tree.command(name="ranking_typerow", description="Pokazuje ranking typerów")
async def ranking_typerow(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    await safe_interaction_send(interaction, embed=typer_ranking_embed(interaction.guild))


@bot.tree.command(name="profil_typera", description="Pokazuje profil typerski wybranego użytkownika")
@app_commands.describe(uzytkownik="Użytkownik do sprawdzenia")
async def profil_typera(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    await safe_interaction_send(interaction, embed=user_typer_stats_embed(interaction.guild, uzytkownik.id))


@bot.tree.command(name="moje_staty_typerskie", description="Pokazuje Twoje statystyki obstawiania")
async def moje_staty_typerskie(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    await safe_interaction_send(interaction, embed=user_typer_stats_embed(interaction.guild, interaction.user.id), ephemeral=True)


@bot.tree.command(name="panel_live_mecze", description="Odświeża panel live wyników w kanale obstawiania")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel_live_mecze(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return
    await refresh_live_results_panel(interaction.guild, force=True)
    await safe_interaction_send(interaction, content="✅ Panel live wyników został odświeżony.", ephemeral=True)


@bot.tree.command(name="panel_obstawiania", description="Wysyła lub odświeża panel obstawiania meczy")
@app_commands.checks.has_permissions(manage_guild=True)
async def panel_obstawiania(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    panel_channel_id = get_betting_panel_channel_id(interaction.guild.id)
    if panel_channel_id is not None and interaction.channel_id != panel_channel_id:
        await safe_interaction_send(interaction, content=f"❌ Panel obstawiania ustawiaj tylko w kanale <#{panel_channel_id}>.", ephemeral=True)
        return

    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)
    await safe_interaction_send(interaction, content="✅ Panel obstawiania został ustawiony / odświeżony.", ephemeral=True)


@bot.tree.command(name="dodaj_mecz", description="Dodaje mecz do obstawiania")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(
    gospodarze="Nazwa gospodarzy",
    goscie="Nazwa gości",
    start_unix="Czas startu meczu jako UNIX timestamp",
    kurs_1="Kurs na 1",
    kurs_x="Kurs na X",
    kurs_2="Kurs na 2",
)
async def dodaj_mecz(
    interaction: discord.Interaction,
    gospodarze: str,
    goscie: str,
    start_unix: int,
    kurs_1: float,
    kurs_x: float,
    kurs_2: float,
):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    open_matches = list_betting_matches(interaction.guild.id, status="open", limit=BETTING_MAX_OPEN_MATCHES_PER_GUILD + 5)
    if len(open_matches) >= BETTING_MAX_OPEN_MATCHES_PER_GUILD:
        await safe_interaction_send(interaction, content="❌ Osiągnięto limit otwartych meczów.", ephemeral=True)
        return

    if kurs_1 <= 1 or kurs_x <= 1 or kurs_2 <= 1:
        await safe_interaction_send(interaction, content="❌ Każdy kurs musi być większy od 1.00.", ephemeral=True)
        return

    try:
        match_id = create_betting_match(
            interaction.guild.id,
            gospodarze.strip(),
            goscie.strip(),
            int(start_unix),
            float(kurs_1),
            float(kurs_x),
            float(kurs_2),
            interaction.user.id,
        )
    except Exception as e:
        await safe_interaction_send(interaction, content=f"❌ Nie udało się dodać meczu: {e}", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, match_id)
    if not match_row:
        await safe_interaction_send(interaction, content="❌ Mecz został dodany, ale nie udało się go odczytać z bazy.", ephemeral=True)
        return

    await safe_interaction_send(interaction, embed=betting_match_embed(match_row), ephemeral=False)


@bot.tree.command(name="lista_meczy", description="Pokazuje listę meczów do obstawiania")
@app_commands.describe(status="open, closed albo settled")
async def lista_meczy(interaction: discord.Interaction, status: str | None = None):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    status_value = status.lower().strip() if status else None
    if status_value not in (None, "open", "closed", "settled"):
        await safe_interaction_send(interaction, content="❌ Dozwolone statusy: open, closed, settled.", ephemeral=True)
        return

    rows = list_betting_matches(interaction.guild.id, status=status_value, limit=20)
    await safe_interaction_send(interaction, embed=betting_list_embed(rows), ephemeral=False)


@bot.tree.command(name="obstaw", description="Obstawia mecz za punkty")
@app_commands.describe(
    mecz_id="ID meczu",
    typ="1, X albo 2",
    stawka="Ile punktów chcesz postawić",
)
async def obstaw(interaction: discord.Interaction, mecz_id: int, typ: str, stawka: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    bets_channel_id = get_betting_bets_channel_id(interaction.guild.id) or get_betting_panel_channel_id(interaction.guild.id)
    if bets_channel_id is not None and interaction.channel_id != bets_channel_id:
        await safe_interaction_send(interaction, content=f"❌ Obstawianie działa tylko w kanale <#{bets_channel_id}>.", ephemeral=True)
        return

    pick = typ.upper().strip()
    if pick not in {"1", "X", "2"}:
        await safe_interaction_send(interaction, content="❌ Typ musi być: 1, X albo 2.", ephemeral=True)
        return

    if stawka < BETTING_MIN_STAKE:
        await safe_interaction_send(interaction, content=f"❌ Minimalna stawka to {BETTING_MIN_STAKE} pkt.", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    if not match_row:
        await safe_interaction_send(interaction, content="❌ Nie znaleziono meczu.", ephemeral=True)
        return

    if match_row["status"] != "open":
        await safe_interaction_send(interaction, content="❌ Ten mecz nie jest już otwarty do obstawiania.", ephemeral=True)
        return

    if int(match_row["start_ts"]) <= int(time.time()):
        await safe_interaction_send(interaction, content="❌ Czas obstawiania minął.", ephemeral=True)
        return

    existing_bet = get_user_bet(interaction.guild.id, mecz_id, interaction.user.id)
    if existing_bet:
        await safe_interaction_send(interaction, content="❌ Już obstawiłeś ten mecz.", ephemeral=True)
        return

    points_row = get_points_row(interaction.guild.id, interaction.user.id)
    total_points = int(points_row["total_points"]) if points_row else 0
    if total_points < stawka:
        await safe_interaction_send(interaction, content="❌ Nie masz tyle punktów.", ephemeral=True)
        return

    odds = get_bet_odds_for_pick(match_row, pick)
    potential_win = int(round(stawka * odds))

    inserted = place_bet(interaction.guild.id, mecz_id, interaction.user.id, pick, stawka, potential_win)
    if not inserted:
        await safe_interaction_send(interaction, content="❌ Nie udało się zapisać zakładu.", ephemeral=True)
        return

    remove_total_points(interaction.guild.id, interaction.user.id, stawka)

    embed = discord.Embed(title="✅ Zakład przyjęty", color=discord.Color.green())
    embed.add_field(name="Mecz", value=f"#{mecz_id} | {match_row['home_team']} vs {match_row['away_team']}", inline=False)
    embed.add_field(name="Typ", value=pick, inline=True)
    embed.add_field(name="Stawka", value=f"{stawka} pkt", inline=True)
    embed.add_field(name="Możliwa wygrana", value=f"{potential_win} pkt", inline=True)
    await safe_interaction_send(interaction, embed=embed, ephemeral=True)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)


@bot.tree.command(name="obstaw_dokladny_wynik", description="Obstawia dokładny wynik meczu za punkty")
@app_commands.describe(
    mecz_id="ID meczu",
    gole_gospodarzy="Ile goli strzelą gospodarze",
    gole_gosci="Ile goli strzelą goście",
    stawka="Ile punktów chcesz postawić",
)
async def obstaw_dokladny_wynik(interaction: discord.Interaction, mecz_id: int, gole_gospodarzy: int, gole_gosci: int, stawka: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    bets_channel_id = get_betting_bets_channel_id(interaction.guild.id) or get_betting_panel_channel_id(interaction.guild.id)
    if bets_channel_id is not None and interaction.channel_id != bets_channel_id:
        await safe_interaction_send(interaction, content=f"❌ Obstawianie działa tylko w kanale <#{bets_channel_id}>.", ephemeral=True)
        return

    if gole_gospodarzy < 0 or gole_gosci < 0:
        await safe_interaction_send(interaction, content="❌ Liczba goli nie może być ujemna.", ephemeral=True)
        return

    if stawka < BETTING_MIN_STAKE:
        await safe_interaction_send(interaction, content=f"❌ Minimalna stawka to {BETTING_MIN_STAKE} pkt.", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    if not match_row:
        await safe_interaction_send(interaction, content="❌ Nie znaleziono meczu.", ephemeral=True)
        return

    if match_row["status"] != "open":
        await safe_interaction_send(interaction, content="❌ Ten mecz nie jest już otwarty do obstawiania.", ephemeral=True)
        return

    if int(match_row["start_ts"]) <= int(time.time()):
        await safe_interaction_send(interaction, content="❌ Czas obstawiania minął.", ephemeral=True)
        return

    existing_bet = get_user_bet(interaction.guild.id, mecz_id, interaction.user.id)
    if existing_bet:
        await safe_interaction_send(interaction, content="❌ Już obstawiłeś ten mecz.", ephemeral=True)
        return

    points_row = get_points_row(interaction.guild.id, interaction.user.id)
    total_points = int(points_row["total_points"]) if points_row else 0
    if total_points < stawka:
        await safe_interaction_send(interaction, content="❌ Nie masz tyle punktów.", ephemeral=True)
        return

    pick = f"SCORE:{gole_gospodarzy}-{gole_gosci}"
    odds = get_bet_odds_for_pick(match_row, pick)
    potential_win = int(round(stawka * odds))

    inserted = place_bet(interaction.guild.id, mecz_id, interaction.user.id, pick, stawka, potential_win)
    if not inserted:
        await safe_interaction_send(interaction, content="❌ Nie udało się zapisać zakładu.", ephemeral=True)
        return

    remove_total_points(interaction.guild.id, interaction.user.id, stawka)

    embed = discord.Embed(title="✅ Zakład na dokładny wynik przyjęty", color=discord.Color.green())
    embed.add_field(name="Mecz", value=f"#{mecz_id} | {match_row['home_team']} vs {match_row['away_team']}", inline=False)
    embed.add_field(name="Typ", value=f"{gole_gospodarzy}:{gole_gosci}", inline=True)
    embed.add_field(name="Kurs", value=f"{odds:.2f}", inline=True)
    embed.add_field(name="Stawka", value=f"{stawka} pkt", inline=True)
    embed.add_field(name="Możliwa wygrana", value=f"{potential_win} pkt", inline=False)
    await safe_interaction_send(interaction, embed=embed, ephemeral=True)


@bot.tree.command(name="moje_typy", description="Pokazuje Twoje obstawione mecze")
async def moje_typy(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    rows = list_user_bets(interaction.guild.id, interaction.user.id, limit=20)
    await safe_interaction_send(interaction, embed=my_bets_embed(rows), ephemeral=True)


@bot.tree.command(name="zamknij_obstawianie", description="Zamyka obstawianie dla meczu")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(mecz_id="ID meczu")
async def zamknij_obstawianie(interaction: discord.Interaction, mecz_id: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    changed = close_betting_match(interaction.guild.id, mecz_id)
    if not changed:
        await safe_interaction_send(interaction, content="❌ Nie udało się zamknąć obstawiania. Sprawdź ID meczu lub status.", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    await safe_interaction_send(interaction, embed=betting_match_embed(match_row), ephemeral=False)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)


@bot.tree.command(name="wynik_dokladny_meczu", description="Ustawia dokładny wynik meczu i rozlicza także zakłady na dokładny wynik")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(mecz_id="ID meczu", gole_gospodarzy="Gole gospodarzy", gole_gosci="Gole gości")
async def wynik_dokladny_meczu(interaction: discord.Interaction, mecz_id: int, gole_gospodarzy: int, gole_gosci: int):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    if not match_row:
        await safe_interaction_send(interaction, content="❌ Nie znaleziono meczu.", ephemeral=True)
        return

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE betting_matches
        SET home_score = ?, away_score = ?
        WHERE guild_id = ? AND match_id = ?
    """), (int(gole_gospodarzy), int(gole_gosci), interaction.guild.id, mecz_id))
    conn.commit()
    conn.close()

    if gole_gospodarzy > gole_gosci:
        result = "1"
    elif gole_gospodarzy == gole_gosci:
        result = "X"
    else:
        result = "2"

    try:
        winners, total_paid = settle_betting_match(interaction.guild.id, mecz_id, result)
    except ValueError as e:
        await safe_interaction_send(interaction, content=f"❌ {e}", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    embed = betting_match_embed(match_row)
    embed.add_field(
        name="Rozliczenie",
        value=f"Wynik dokładny: **{gole_gospodarzy}:{gole_gosci}**\n1X2: **{result}**\nWygrani: **{winners}**\nWypłacono: **{total_paid} pkt**",
        inline=False
    )
    await safe_interaction_send(interaction, embed=embed, ephemeral=False)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)


@bot.tree.command(name="wynik_meczu", description="Rozlicza mecz i wypłaca wygrane")
@app_commands.checks.has_permissions(manage_guild=True)
@app_commands.describe(mecz_id="ID meczu", wynik="1, X albo 2")
async def wynik_meczu(interaction: discord.Interaction, mecz_id: int, wynik: str):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    result = wynik.upper().strip()
    if result not in {"1", "X", "2"}:
        await safe_interaction_send(interaction, content="❌ Wynik musi być: 1, X albo 2.", ephemeral=True)
        return

    try:
        winners, total_paid = settle_betting_match(interaction.guild.id, mecz_id, result)
    except ValueError as e:
        await safe_interaction_send(interaction, content=f"❌ {e}", ephemeral=True)
        return

    match_row = get_betting_match(interaction.guild.id, mecz_id)
    embed = betting_match_embed(match_row)
    embed.add_field(name="Rozliczenie", value=f"Wynik: **{result}**\nWygrani: **{winners}**\nWypłacono: **{total_paid} pkt**", inline=False)
    await safe_interaction_send(interaction, embed=embed, ephemeral=False)
    await refresh_betting_panel(interaction.guild, force=True)
    await refresh_live_results_panel(interaction.guild, force=True)
    await refresh_betting_side_panels(interaction.guild, force=True)

@bot.tree.command(name="odswiez_panele", description="Odświeża wszystkie panele bota")
@app_commands.checks.has_permissions(manage_guild=True)
async def odswiez_panele(interaction: discord.Interaction):
    if interaction.guild is None:
        await safe_interaction_send(interaction, content="Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

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
