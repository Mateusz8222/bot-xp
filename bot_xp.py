import os
import time
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

# =========================================================
# AUTO PRYWATNE KANAŁY
# =========================================================
PRIVATE_CHANNEL_CATEGORY_NAME = "🔒 Prywatne kanały"
PRIVATE_CHANNEL_PREFIX = "🔒・"
PRIVATE_CHANNEL_TOPIC = "Kanał prywatny utworzony automatycznie po zakupie w sklepie."

# =========================================================
# ID RÓL
# =========================================================
VIP_ROLE_ID = 1474567627895738388
LEGEND_ROLE_ID = 1490683484262498335
PRIVATE_CHANNEL_ROLE_ID = 1475970739986239620  # 🔑 moderator kanału prywatnego

# =========================================================
# USTAWIENIA XP
# =========================================================
TEXT_MESSAGES_REQUIRED = 10
TEXT_POINTS = 2

VC_INTERVAL_SECONDS = 600  # 10 minut
VC_POINTS_SOLO = 5
VC_POINTS_WITH_ACTIVE = 10

VIP_MULTIPLIER = 1.20
LEGEND_MULTIPLIER = 1.40

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
    "prywatny_kanal": {
        "price": 30000,
        "role_id": PRIVATE_CHANNEL_ROLE_ID,
        "label": "🔒 Dostęp do prywatnego kanału",
    },
    "auto_prywatny_kanal": {
        "price": 30000,
        "role_id": PRIVATE_CHANNEL_ROLE_ID,
        "label": "🛠️ Auto prywatny kanał",
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

    conn.commit()
    conn.close()


def fetchone_dict(cur):
    row = cur.fetchone()
    if row is None:
        return None
    return dict(row)


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
    total_add = text_points + voice_points

    conn = db_connect()
    cur = conn.cursor()
    cur.execute(sql("""
        UPDATE points
        SET text_points = text_points + ?,
            voice_points = voice_points + ?,
            total_points = total_points + ?
        WHERE guild_id = ? AND user_id = ?
    """), (text_points, voice_points, total_add, guild_id, user_id))
    conn.commit()
    conn.close()


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
    """), (amount, amount, guild_id, user_id))
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
    multiplier = get_member_multiplier(member)
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
    return ""


def points_embed_for_user(member: discord.Member, row: dict) -> discord.Embed:
    embed = discord.Embed(title="🏆 Twoje punkty", color=discord.Color.blurple())
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)
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
        member = guild.get_member(int(row["user_id"]))
        name = member.display_name if member else f"Użytkownik {row['user_id']}"
        prefix = get_rank_prefix(member)
        lines.append(
            f"**{index}.** {prefix}{name} — **{row['total_points']} pkt** "
            f"(💬 {row['text_points']} | 🎤 {row['voice_points']} | 📝 {row['message_count']})"
        )

    embed.description = "\n".join(lines)
    return embed


def xpinfo_embed() -> discord.Embed:
    embed = discord.Embed(title="📘 Zasady punktów", color=discord.Color.orange())
    embed.add_field(name="💬 Wiadomości", value="2 punkty za każde 10 wiadomości", inline=False)
    embed.add_field(
        name="🎤 VC",
        value="5 punktów za 10 minut solo\n10 punktów za 10 minut z aktywną osobą",
        inline=False,
    )
    embed.add_field(name="⭐ Bonusy rang", value="VIP: +20%\nLEGENDA: +40%", inline=False)
    embed.add_field(name="❌ Punkty VC nie lecą gdy", value="bot / mute / deaf / kanał AFK", inline=False)
    return embed


def shop_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🛒 Sklep punktów",
        description="Kupuj role za punkty aktywności.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="⭐ VIP", value="Cena: **50 000 pkt**", inline=False)
    embed.add_field(name="💎 LEGENDA", value="Cena: **100 000 pkt**", inline=False)
    embed.add_field(name="🔒 Prywatny kanał", value="Cena: **30 000 pkt**", inline=False)
    embed.add_field(name="🛠️ Auto prywatny kanał", value="Cena: **30 000 pkt**", inline=False)
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
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        member: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            attach_files=True,
            embed_links=True,
            add_reactions=True,
        ),
    }
    if bot_member is not None:
        overwrites[bot_member] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            manage_messages=True,
            read_message_history=True,
        )

    role = guild.get_role(PRIVATE_CHANNEL_ROLE_ID)
    if role is not None:
        overwrites[role] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
        )

    channel = await guild.create_voice_channel(
        name=expected_name,
        category=category,
        topic=PRIVATE_CHANNEL_TOPIC,
        overwrites=overwrites,
        reason=f"Auto prywatny kanał dla {member}",
    )

    return channel


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
    role = interaction.guild.get_role(item["role_id"])

    if member is None:
        await safe_interaction_send(interaction, content="❌ Nie udało się znaleźć użytkownika.", ephemeral=True)
        return

    if role is None:
        await safe_interaction_send(interaction, content="❌ Nie udało się znaleźć roli sklepowej.", ephemeral=True)
        return

    row = get_points_row(interaction.guild.id, member.id)
    if row is None:
        await safe_interaction_send(interaction, content="❌ Nie masz jeszcze punktów.", ephemeral=True)
        return

    if int(row["total_points"]) < int(item["price"]):
        await safe_interaction_send(
            interaction,
            content=f"❌ Za mało punktów. Potrzebujesz **{item['price']} pkt**.",
            ephemeral=True
        )
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
                    content=f"❌ Masz już prywatny kanał: {existing_channel.mention}",
                    ephemeral=True,
                )
                return
        except Exception:
            pass

    elif role in member.roles:
        await safe_interaction_send(interaction, content="❌ Masz już tę rolę.", ephemeral=True)
        return

    try:
        if role.id == LEGEND_ROLE_ID:
            vip_role = interaction.guild.get_role(VIP_ROLE_ID)
            if vip_role and vip_role in member.roles:
                await member.remove_roles(vip_role, reason="Awans na LEGENDĘ")

        created_channel = None

        if item_key == "auto_prywatny_kanal":
            await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")
            created_channel = await create_or_get_private_channel_for_member(interaction.guild, member)
        else:
            await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")

        remove_total_points(interaction.guild.id, member.id, int(item["price"]))

        embed = discord.Embed(
            title="✅ Zakup udany",
            description=f"Kupiłeś **{item['label']}** za **{item['price']} pkt**.",
            color=discord.Color.green()
        )

        if role.id == LEGEND_ROLE_ID:
            embed.add_field(name="💎 Bonus Legendy", value="Masz teraz +40% punktów i dostęp do kanałów legendy.", inline=False)
        elif role.id == VIP_ROLE_ID:
            embed.add_field(name="⭐ Bonus VIP", value="Masz teraz +20% punktów.", inline=False)
        elif item_key == "prywatny_kanal":
            embed.add_field(name="🔒 Dostęp", value="Masz rolę dostępu do prywatnego kanału.", inline=False)
        elif item_key == "auto_prywatny_kanal" and created_channel is not None:
            embed.add_field(name="🛠️ Twój kanał", value=f"Gotowe: {created_channel.mention}", inline=False)

        await safe_interaction_send(interaction, embed=embed, ephemeral=True)

    except discord.Forbidden:
        await safe_interaction_send(
            interaction,
            content="❌ Bot nie może nadać tej roli. Ustaw rolę bota wyżej niż VIP i LEGENDA.",
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

    @discord.ui.button(label="Prywatny kanał", emoji="🔒", style=discord.ButtonStyle.secondary, custom_id="shop_private_channel")
    async def buy_private_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "prywatny_kanal")

    @discord.ui.button(label="Auto kanał", emoji="🛠️", style=discord.ButtonStyle.primary, custom_id="shop_auto_private_channel")
    async def buy_auto_private_channel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await process_shop_purchase(interaction, "auto_prywatny_kanal")

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

        add_points_with_role_bonus(member, voice_points=full_intervals * base_points)

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
