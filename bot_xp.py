import os
import time
import sqlite3
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = os.getenv("TOKEN")
DB_FILE = "xp.db"

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
}

# panel_key -> channel_id
PANEL_CHANNELS = {
    "points": POINTS_CHANNEL_ID,
    "ranking": RANKING_CHANNEL_ID,
    "xpinfo": XPINFO_CHANNEL_ID,
    "shop": SHOP_CHANNEL_ID,
}

# =========================================================
# BAZA
# =========================================================
def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
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


def ensure_user_row(guild_id: int, user_id: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT OR IGNORE INTO points (
            guild_id, user_id, text_points, voice_points, total_points, message_count
        ) VALUES (?, ?, 0, 0, 0, 0)
    """, (guild_id, user_id))
    conn.commit()
    conn.close()


def get_points_row(guild_id: int, user_id: int) -> Optional[sqlite3.Row]:
    ensure_user_row(guild_id, user_id)
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT text_points, voice_points, total_points, message_count
        FROM points
        WHERE guild_id = ? AND user_id = ?
    """, (guild_id, user_id))
    row = cur.fetchone()
    conn.close()
    return row


def update_message_count(guild_id: int, user_id: int) -> int:
    ensure_user_row(guild_id, user_id)

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
    total_add = text_points + voice_points

    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET text_points = text_points + ?,
            voice_points = voice_points + ?,
            total_points = total_points + ?
        WHERE guild_id = ? AND user_id = ?
    """, (text_points, voice_points, total_add, guild_id, user_id))
    conn.commit()
    conn.close()


def remove_total_points(guild_id: int, user_id: int, amount: int) -> None:
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        UPDATE points
        SET total_points = total_points - ?
        WHERE guild_id = ? AND user_id = ?
    """, (amount, guild_id, user_id))
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
        self.add_view(UtilityView(self))


bot = XPBot()

# =========================================================
# POMOCNICZE
# =========================================================
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
    count = 0
    for member in channel.members:
        if is_active_for_vc(member):
            count += 1
    return count


def get_rank_prefix(member: Optional[discord.Member]) -> str:
    if member is None:
        return ""

    role_ids = {role.id for role in member.roles}

    if LEGEND_ROLE_ID in role_ids:
        return "💎 "
    if VIP_ROLE_ID in role_ids:
        return "⭐ "
    return ""


def points_embed_for_user(member: discord.Member, row: sqlite3.Row) -> discord.Embed:
    embed = discord.Embed(
        title="🏆 Twoje punkty",
        color=discord.Color.blurple()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)
    embed.set_footer(text=f"Użytkownik: {member.display_name}")
    return embed


def ranking_embed(guild: discord.Guild) -> discord.Embed:
    rows = get_top_users(guild.id, 10)
    embed = discord.Embed(
        title="🏆 Ranking serwera",
        color=discord.Color.gold()
    )

    if not rows:
        embed.description = "Na tym serwerze nikt nie ma jeszcze punktów."
        return embed

    lines = []
    for index, row in enumerate(rows, start=1):
        member = guild.get_member(row["user_id"])
        name = member.display_name if member else f"Użytkownik {row['user_id']}"
        prefix = get_rank_prefix(member)

        lines.append(
            f"**{index}.** {prefix}{name} — **{row['total_points']} pkt** "
            f"(💬 {row['text_points']} | 🎤 {row['voice_points']} | 📝 {row['message_count']})"
        )

    embed.description = "\n".join(lines)
    return embed


def xpinfo_embed() -> discord.Embed:
    embed = discord.Embed(
        title="📘 Zasady punktów",
        color=discord.Color.orange()
    )
    embed.add_field(
        name="💬 Wiadomości",
        value="2 punkty za każde 10 wiadomości",
        inline=False
    )
    embed.add_field(
        name="🎤 VC",
        value="5 punktów za 10 minut solo\n10 punktów za 10 minut z aktywną osobą",
        inline=False
    )
    embed.add_field(
        name="⭐ Bonusy rang",
        value="VIP: +20%\nLEGENDA: +40%",
        inline=False
    )
    embed.add_field(
        name="❌ Punkty VC nie lecą gdy",
        value="bot / mute / deaf / kanał AFK",
        inline=False
    )
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
        except discord.NotFound:
            message = None
        except discord.HTTPException:
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
        await interaction.response.send_message("Ta akcja działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Kupowanie działa tylko w kanale 🛒・sklep.",
            ephemeral=True
        )
        return

    item_key = item_name.lower().strip()
    item = SHOP_ITEMS.get(item_key)

    if item is None:
        await interaction.response.send_message("❌ Nie ma takiego przedmiotu.", ephemeral=True)
        return

    member = interaction.guild.get_member(interaction.user.id)
    role = interaction.guild.get_role(item["role_id"])

    if member is None or role is None:
        await interaction.response.send_message(
            "❌ Nie udało się znaleźć użytkownika lub roli.",
            ephemeral=True
        )
        return

    row = get_points_row(interaction.guild.id, member.id)
    if row is None:
        await interaction.response.send_message("❌ Nie masz jeszcze punktów.", ephemeral=True)
        return

    if row["total_points"] < item["price"]:
        await interaction.response.send_message(
            f"❌ Za mało punktów. Potrzebujesz **{item['price']} pkt**.",
            ephemeral=True
        )
        return

    if role in member.roles:
        await interaction.response.send_message(
            "❌ Masz już tę rolę.",
            ephemeral=True
        )
        return

    try:
        # Jeśli kupuje LEGENDĘ, zdejmujemy VIP
        if role.id == LEGEND_ROLE_ID:
            vip_role = interaction.guild.get_role(VIP_ROLE_ID)
            if vip_role and vip_role in member.roles:
                await member.remove_roles(vip_role, reason="Awans na LEGENDĘ")

        await member.add_roles(role, reason=f"Zakup w sklepie: {item_key}")
        remove_total_points(interaction.guild.id, member.id, item["price"])

        embed = discord.Embed(
            title="✅ Zakup udany",
            description=f"Kupiłeś **{item['label']}** za **{item['price']} pkt**.",
            color=discord.Color.green()
        )

        if role.id == LEGEND_ROLE_ID:
            embed.add_field(
                name="💎 Bonus Legendy",
                value="Masz teraz +40% punktów i dostęp do kanałów legendy.",
                inline=False
            )
        elif role.id == VIP_ROLE_ID:
            embed.add_field(
                name="⭐ Bonus VIP",
                value="Masz teraz +20% punktów.",
                inline=False
            )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message(
            "❌ Bot nie może nadać tej roli. Ustaw rolę bota wyżej niż VIP i LEGENDA.",
            ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Błąd przy zakupie: {e}",
            ephemeral=True
        )

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
            await interaction.response.send_message("Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        row = get_points_row(interaction.guild.id, interaction.user.id)
        member = interaction.guild.get_member(interaction.user.id)
        if row is None or member is None:
            await interaction.response.send_message("Nie masz jeszcze punktów.", ephemeral=True)
            return

        await interaction.response.send_message(embed=points_embed_for_user(member, row), ephemeral=True)

    @discord.ui.button(label="🏆 Pokaż ranking", style=discord.ButtonStyle.success, custom_id="xp_ranking_button")
    async def ranking_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Ta akcja działa tylko na serwerze.", ephemeral=True)
            return

        await interaction.response.send_message(embed=ranking_embed(interaction.guild), ephemeral=True)

    @discord.ui.button(label="📘 Zasady XP", style=discord.ButtonStyle.secondary, custom_id="xp_info_button")
    async def info_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=xpinfo_embed(), ephemeral=True)


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
    if message.author.bot or message.guild is None:
        return

    if not message.content or not message.content.strip():
        return

    count = update_message_count(message.guild.id, message.author.id)

    if count % TEXT_MESSAGES_REQUIRED == 0:
        member = message.guild.get_member(message.author.id)
        if member:
            add_points_with_role_bonus(member, text_points=TEXT_POINTS)

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
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

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
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != POINTS_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Użyj tej komendy w kanale 📊・sprawdz-punkty.",
            ephemeral=True
        )
        return

    row = get_points_row(interaction.guild.id, interaction.user.id)
    member = interaction.guild.get_member(interaction.user.id)

    if row is None or member is None:
        await interaction.response.send_message("Nie masz jeszcze żadnych punktów.", ephemeral=True)
        return

    await interaction.response.send_message(
        embed=points_embed_for_user(member, row),
        ephemeral=True
    )


@bot.tree.command(name="punkty_uzytkownika", description="Pokazuje punkty wybranego użytkownika")
@app_commands.describe(uzytkownik="Wybierz użytkownika")
async def punkty_uzytkownika(interaction: discord.Interaction, uzytkownik: discord.Member):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != POINTS_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Użyj tej komendy w kanale 📊・sprawdz-punkty.",
            ephemeral=True
        )
        return

    row = get_points_row(interaction.guild.id, uzytkownik.id)
    if row is None:
        await interaction.response.send_message("Ten użytkownik nie ma jeszcze punktów.", ephemeral=True)
        return

    embed = discord.Embed(
        title=f"🏆 Punkty użytkownika: {uzytkownik.display_name}",
        color=discord.Color.green()
    )
    embed.add_field(name="💬 Za wiadomości", value=str(row["text_points"]), inline=False)
    embed.add_field(name="🎤 Za VC", value=str(row["voice_points"]), inline=False)
    embed.add_field(name="⭐ Razem", value=str(row["total_points"]), inline=False)
    embed.add_field(name="📝 Liczba wiadomości", value=str(row["message_count"]), inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="ranking", description="Pokazuje ranking serwera")
async def ranking(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != RANKING_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Użyj tej komendy w kanale 🏆・ranking.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(embed=ranking_embed(interaction.guild))


@bot.tree.command(name="xpinfo", description="Pokazuje zasady punktów")
async def xpinfo(interaction: discord.Interaction):
    if interaction.channel_id != XPINFO_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Użyj tej komendy w kanale 📘・info-xp.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(embed=xpinfo_embed())


@bot.tree.command(name="sklep", description="Pokazuje sklep punktów")
async def sklep(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    if interaction.channel_id != SHOP_CHANNEL_ID:
        await interaction.response.send_message(
            "❌ Użyj tej komendy w kanale 🛒・sklep.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(embed=shop_embed(), view=ShopView(bot))


@bot.tree.command(name="kup", description="Kup przedmiot ze sklepu")
@app_commands.describe(przedmiot="vip albo legenda")
async def kup(interaction: discord.Interaction, przedmiot: str):
    await process_shop_purchase(interaction, przedmiot)


@bot.tree.command(name="odswiez_panele", description="Odświeża wszystkie panele bota")
@app_commands.checks.has_permissions(manage_guild=True)
async def odswiez_panele(interaction: discord.Interaction):
    if interaction.guild is None:
        await interaction.response.send_message("Ta komenda działa tylko na serwerze.", ephemeral=True)
        return

    await refresh_all_panels(interaction.guild)
    await interaction.response.send_message("✅ Panele zostały odświeżone.", ephemeral=True)


@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ Błąd komendy: {error}", ephemeral=True)
    except discord.InteractionResponded:
        await interaction.followup.send(f"❌ Błąd komendy: {error}", ephemeral=True)

# =========================================================
# START
# =========================================================
def main() -> None:
    if not TOKEN:
        raise RuntimeError("Brak zmiennej TOKEN w Railway.")
    init_db()
    bot.run(TOKEN)


if __name__ == "__main__":
    main()
