import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# -----------------------------
# CONFIG LADEN
# -----------------------------
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

TOKEN = config["token"]

# -----------------------------
# DATEIEN
# -----------------------------
HAEUSER_DATEI = "haeuser.json"
XP_DATEI = "xp.json"

# -----------------------------
# INTENTS
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

def ist_teammitglied(interaction: discord.Interaction):
    return any(role.id == config["admin_rolle"] for role in interaction.user.roles)

# -----------------------------
# JSON FUNKTIONEN
# -----------------------------
def lade_haeuser():
    if not os.path.exists(HAEUSER_DATEI):
        return {}

    with open(HAEUSER_DATEI, "r", encoding="utf-8") as f:
        return json.load(f)


def speicher_haeuser(daten):
    with open(HAEUSER_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)


def lade_xp():
    if not os.path.exists(XP_DATEI):
        return {"users": {}}

    with open(XP_DATEI, "r", encoding="utf-8") as f:
        return json.load(f)


def speicher_xp(daten):
    with open(XP_DATEI, "w", encoding="utf-8") as f:
        json.dump(daten, f, indent=4, ensure_ascii=False)

# -----------------------------
# BOT ONLINE
# -----------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()

    print("--------------------------------")
    print(f"Bot: {bot.user}")
    print("Immobilien-System geladen")
    print("XP-System geladen")
    print("Slash Commands synchronisiert")
    print("--------------------------------")

# -----------------------------
# HIER KOMMEN IM NÄCHSTEN TEIL:
#
# /liste
# /vergeben
# /freigeben
#
# /discordkontrolle
# /xp
# /rangliste
# /xpadd
# /xpremove
# /xpreset
#
# -----------------------------

# NextLife RP|VC Immobilien Bot (Grundgerüst)


TOKEN = "MTUxNTM1MTc3MzM0OTY3OTMxNQ.GRVuq_.V_S_9-mDZZWfo46_nM_9quaLXa-ou_1et3dObk"
DATEI = "haeuser.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

LISTE_MESSAGE = None


def lade():
    with open(DATEI, "r", encoding="utf-8") as f:
        return json.load(f)


def speichern(data):
    with open(DATEI, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def baue_embed():
    daten = lade()

    embed = discord.Embed(
        title="🏘️ NextLife RP | Immobilienverwaltung",
        description="🟢 Frei | 🔴 Vergeben",
        color=0x2ECC71
    )

    kategorien = [
        ("☠️ Gang-Gebiete", "G"),
        ("🏪 Läden & Flächen", "L"),
        ("🏛️ Staatliche Grundstücke", "S"),
        ("🏠 Häuser & Basketballplatz", "H"),
    ]

    for name, prefix in kategorien:
        text = ""
        keys = sorted(
            [k for k in daten if k.startswith(prefix)],
            key=lambda x: int(x[1:])
        )
        for k in keys:
            preis = daten[k]["preis"]
            besitzer = daten[k]["besitzer"]
            status = "🟢 Frei" if besitzer == "Frei" else f"🔴 {besitzer}"
            text += f"**{k}** • 💰 {preis}/Woche • {status}\n"

        embed.add_field(name=name, value=text or "-", inline=False)

    embed.set_footer(text="NextLife RP | VC   • Immobilienverwaltung")
    return embed


@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} ist online!")


@bot.tree.command(
    name="liste",
    description="Immobilien anzeigen"
)
@app_commands.check(ist_teammitglied)
async def liste(interaction: discord.Interaction):
    global LISTE_MESSAGE

    embed = baue_embed()

    await interaction.response.send_message(embed=embed)

    await bot_log(
        interaction,
        "📋 Hat die Immobilienliste geöffnet."
    )

    LISTE_MESSAGE = await interaction.original_response()


@bot.tree.command(
    name="vergeben",
    description="Immobilie vergeben"
)
@app_commands.check(ist_teammitglied)
async def vergeben(
    interaction: discord.Interaction,
    immobilie: str,
    user: discord.Member
):
    global LISTE_MESSAGE


    immobilie = immobilie.upper()
    daten = lade()

    if immobilie not in daten:
        await interaction.response.send_message("❌ Immobilie existiert nicht.", ephemeral=True)
        return

    daten[immobilie]["besitzer"] = user.mention
    speichern(daten)
    await aktualisiere_immobilienliste()

    if LISTE_MESSAGE:
        await LISTE_MESSAGE.edit(embed=baue_embed())

    await interaction.response.send_message(f"✅ {immobilie} wurde an {user.mention} vergeben.")

    await bot_log(
        interaction,
        f"🏠 Hat **{immobilie}** an {user.mention} vergeben."
    )


@bot.tree.command(name="freigeben", description="Immobilie freigeben")
@app_commands.check(ist_teammitglied)
async def freigeben(interaction: discord.Interaction, immobilie: str):
    global LISTE_MESSAGE

    immobilie = immobilie.upper()
    daten = lade()

    if immobilie not in daten:
        await interaction.response.send_message("❌ Immobilie existiert nicht.", ephemeral=True)
        return

    daten[immobilie]["besitzer"] = "Frei"
    speichern(daten)
    await aktualisiere_immobilienliste()

    if LISTE_MESSAGE:
        await LISTE_MESSAGE.edit(embed=baue_embed())

    await interaction.response.send_message(f"✅ {immobilie} wurde freigegeben.")

    await bot_log(
        interaction,
        f"🟢 Hat **{immobilie}** freigegeben."
    )

# ==================================================
# DISCORD-KONTROLLE
# ==================================================

@bot.tree.command(
    name="discordkontrolle",
    description="Kontrolliert einen Benutzer und vergibt XP an den Supporter."
)
@app_commands.check(ist_teammitglied)
async def discordkontrolle(
    interaction: discord.Interaction,
    user: discord.Member
):

    # Prüfen, ob der Benutzer im aktuellen Kanal geschrieben hat
    gefunden = False

    async for nachricht in interaction.channel.history(limit=100):
        if nachricht.author.id == user.id:
            gefunden = True
            break

    if not gefunden:
        await interaction.response.send_message(
            "❌ Dieser Benutzer hat im aktuellen Kanal keine der letzten 100 Nachrichten geschrieben.",
            ephemeral=True
        )
        return

    daten = lade_xp()

    if "users" not in daten:
        daten["users"] = {}

    supporter = interaction.user
    supporter_id = str(supporter.id)

    if supporter_id not in daten["users"]:
        daten["users"][supporter_id] = {
            "name": supporter.display_name,
            "xp": 0
        }

    daten["users"][supporter_id]["name"] = supporter.display_name
    daten["users"][supporter_id]["xp"] += config["xp_pro_kontrolle"]

    speicher_xp(daten)

    await aktualisiere_rangliste()

    await sende_log(
        supporter,
        user,
        config["xp_pro_kontrolle"]
    )

    # Falls du die Funktion eingebaut hast
    try:
        await aktualisiere_rangliste()
    except:
        pass

    embed = discord.Embed(
        title="✅ Discord-Kontrolle erfolgreich",
        color=0x2ECC71
    )

    embed.add_field(
        name="👤 Kontrollierter Benutzer",
        value=user.mention,
        inline=False
    )

    embed.add_field(
        name="🛡️ Supporter",
        value=supporter.mention,
        inline=False
    )

    embed.add_field(
        name="⭐ Erhaltene XP",
        value=f"+{config['xp_pro_kontrolle']} XP",
        inline=True
    )

    embed.add_field(
        name="🏆 Gesamt-XP",
        value=str(daten["users"][supporter_id]["xp"]),
        inline=True
    )

    await interaction.response.send_message(embed=embed)

    await sende_log(
        supporter,
        user,
        config["xp_pro_kontrolle"]
    )

    await bot_log(
        interaction,
        f"✅ Discord-Kontrolle bei {user.mention} durchgeführt (+{config['xp_pro_kontrolle']} XP)."
    )

@discordkontrolle.error
async def discordkontrolle_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.CheckFailure):
        await interaction.response.send_message(
            "❌ Du hast keine Berechtigung für diesen Befehl.",
            ephemeral=True
        )

# ==================================================
# /xp
# ==================================================

@bot.tree.command(
    name="xp",
    description="Zeigt die XP eines Benutzers."
)
@app_commands.check(ist_teammitglied)
@app_commands.describe(user="Benutzer auswählen")
async def xp(
    interaction: discord.Interaction,
    user: discord.Member
):

    daten = lade_xp()

    if "users" not in daten:
        daten["users"] = {}

    user_id = str(user.id)

    if user_id not in daten["users"]:
        daten["users"][user_id] = {
            "name": user.display_name,
            "xp": 0
        }
        speicher_xp(daten)

    xp = daten["users"][user_id]["xp"]

    embed = discord.Embed(
        title="⭐ XP-Profil",
        color=0xF1C40F
    )

    embed.set_thumbnail(url=user.display_avatar.url)

    embed.add_field(
        name="👤 Benutzer",
        value=user.mention,
        inline=False
    )

    embed.add_field(
        name="⭐ XP",
        value=f"**{xp} XP**",
        inline=False
    )

    embed.set_footer(
        text="NextLife RP | Discord-Kontrolle"
    )

    await interaction.response.send_message(embed=embed)

    await bot_log(
        interaction,
        f"⭐ Hat die XP von {user.mention} angesehen."
    )

# ==================================================
# /rangliste
# ==================================================

@bot.tree.command(
    name="rangliste",
    description="Zeigt die Discord-Kontroll Rangliste."
)
@app_commands.check(ist_teammitglied)
async def rangliste(interaction: discord.Interaction):

    daten = lade_xp()

if "users" not in daten:
    daten["users"] = {}

# Alle Teammitglieder hinzufügen
teamrolle = interaction.guild.get_role(config["admin_rolle"])

if teamrolle:
    for member in teamrolle.members:
        user_id = str(member.id)

        if user_id not in daten["users"]:
            daten["users"][user_id] = {
                "name": member.display_name,
                "xp": 0
            }
        else:
            daten["users"][user_id]["name"] = member.display_name

speicher_xp(daten)

sortiert = sorted(
    daten["users"].items(),
    key=lambda x: x[1]["xp"],
    reverse=True
)

    embed = discord.Embed(
        title="🏆 NextLife RP | Discord-Kontroll Rangliste",
        description="Die aktivsten Teammitglieder",
        color=0xFFD700
    )

    emojis = ["🥇", "🥈", "🥉"]

    text = ""

    for i, (user_id, info) in enumerate(sortiert[:10]):

        if i < 3:
            platz = emojis[i]
        else:
            platz = f"**{i+1}.**"

        text += (
            f"{platz} {info['name']}\n"
            f"⭐ **{info['xp']} XP**\n\n"
        )

    embed.add_field(
        name="Top 10",
        value=text,
        inline=False
    )

    embed.set_footer(
        text="NextLife RP | Discord-Kontrolle"
    )

    await interaction.response.send_message(embed=embed)

# ==================================================
# /xpadd
# ==================================================

@bot.tree.command(
    name="xpadd",
    description="Fügt einem Benutzer XP hinzu."
)
@app_commands.check(ist_teammitglied)
async def xpadd(
    interaction: discord.Interaction,
    user: discord.Member,
    xp: int
):

    daten = lade_xp()

    if "users" not in daten:
        daten["users"] = {}

    user_id = str(user.id)

    if user_id not in daten["users"]:
        daten["users"][user_id] = {
            "name": user.display_name,
            "xp": 0
        }

    daten["users"][user_id]["name"] = user.display_name
    daten["users"][user_id]["xp"] += xp

    speicher_xp(daten)

    await interaction.response.send_message(
        f"✅ {user.mention} hat **+{xp} XP** erhalten."
    )

    await bot_log(
        interaction,
        f"➕ Hat {user.mention} {xp} XP gegeben."
    )


# ==================================================
# /xpremove
# ==================================================

@bot.tree.command(
    name="xpremove",
    description="Entfernt XP von einem Benutzer."
)
@app_commands.check(ist_teammitglied)
async def xpremove(
    interaction: discord.Interaction,
    user: discord.Member,
    xp: int
):

    daten = lade_xp()

    if "users" not in daten:
        daten["users"] = {}

    user_id = str(user.id)

    if user_id not in daten["users"]:
        daten["users"][user_id] = {
            "name": user.display_name,
            "xp": 0
        }

    daten["users"][user_id]["xp"] -= xp

    if daten["users"][user_id]["xp"] < 0:
        daten["users"][user_id]["xp"] = 0

    speicher_xp(daten)

    await interaction.response.send_message(
        f"➖ {xp} XP wurden von {user.mention} entfernt."
    )

    await bot_log(
        interaction,
        f"➖ Hat {xp} XP von {user.mention} entfernt."
    )

# ==================================================
# /xpreset
# ==================================================

@bot.tree.command(
    name="xpreset",
    description="Setzt die XP eines Benutzers auf 0."
)
@app_commands.check(ist_teammitglied)
async def xpreset(
    interaction: discord.Interaction,
    user: discord.Member
):

    daten = lade_xp()

    if "users" not in daten:
        daten["users"] = {}

    user_id = str(user.id)

    daten["users"][user_id] = {
        "name": user.display_name,
        "xp": 0
    }

    speicher_xp(daten)

    await interaction.response.send_message(
        f"🔄 Die XP von {user.mention} wurden auf **0 XP** zurückgesetzt."
    )

    await bot_log(
        interaction,
        f"🔄 Hat die XP von {user.mention} zurückgesetzt."
    )
# ==================================================
# RANGLISTE AKTUALISIEREN
# ==================================================

async def aktualisiere_rangliste():

    kanal_id = config["rangliste_kanal"]
    nachricht_id = config["rangliste_nachricht"]

    if kanal_id == 0 or nachricht_id == 0:
        return

    kanal = bot.get_channel(kanal_id)

    if kanal is None:
        return

    try:
        nachricht = await kanal.fetch_message(nachricht_id)
    except:
        return

    daten = lade_xp()

    embed = discord.Embed(
        title="🏆 NextLife RP | Discord-Kontroll Rangliste",
        color=0xFFD700
    )

    if "users" not in daten or len(daten["users"]) == 0:

        embed.description = "Noch keine XP vorhanden."

    else:

        sortiert = sorted(
            daten["users"].items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )

        text = ""

        emojis = ["🥇", "🥈", "🥉"]

        for i, (uid, info) in enumerate(sortiert[:10]):

            if i < 3:
                platz = emojis[i]
            else:
                platz = f"**{i+1}.**"

            text += f"{platz} {info['name']} • ⭐ {info['xp']} XP\n"

        embed.description = text

    embed.set_footer(text="Automatisch aktualisiert")

    await nachricht.edit(embed=embed)
# ==================================================
# BOT LOGS
# ==================================================

async def bot_log(interaction: discord.Interaction, aktion: str):

    kanal = bot.get_channel(config["log_kanal"])

    if kanal is None:
        return

    embed = discord.Embed(
        title="📋 Bot-Log",
        color=0x3498DB
    )

    embed.add_field(
        name="👤 Benutzer",
        value=f"{interaction.user.mention}\n`{interaction.user.id}`",
        inline=False
    )

    embed.add_field(
        name="📝 Aktion",
        value=aktion,
        inline=False
    )

    embed.add_field(
        name="📍 Kanal",
        value=interaction.channel.mention,
        inline=True
    )

    embed.add_field(
        name="🖥️ Server",
        value=interaction.guild.name,
        inline=True
    )

    embed.add_field(
        name="🕒 Zeit",
        value=f"<t:{int(discord.utils.utcnow().timestamp())}:F>",
        inline=False
    )

    embed.set_footer(text="NextLife RP | Bot Logs")

    await kanal.send(embed=embed)

bot.run(TOKEN)