import os
import discord
from discord import app_commands
import aiohttp

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_URL = "http://127.0.0.1:5000/push"
SERVER_STOP_URL = "http://127.0.0.1:5000/stop"
SERVER_HEALTH_URL = "http://127.0.0.1:5000/health"
SERVER_PUBLIC_URL = os.getenv("PUBLIC_URL", "http://localhost:5000")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ─────────────────────────────────────────
# /send
# ─────────────────────────────────────────
@tree.command(
    name="send",
    description="Envoie une image/vidéo et/ou un texte sur l'overlay OBS",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    texte="Le texte à afficher sur l'overlay (optionnel)",
    fichier="L'image ou la vidéo à afficher (optionnel)"
)
async def send_command(
    interaction: discord.Interaction,
    texte: str = None,
    fichier: discord.Attachment = None
):
    if not texte and not fichier:
        await interaction.response.send_message(
            "❌ Tu dois fournir au moins un texte ou un fichier !", ephemeral=True
        )
        return

    allowed_extensions = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".webm"]
    media_url = None
    media_type = None

    if fichier:
        ext = "." + fichier.filename.split(".")[-1].lower()
        if ext not in allowed_extensions:
            await interaction.response.send_message(
                f"❌ Format non supporté : `{ext}`\nFormats acceptés : PNG, JPG, GIF, WEBP, MP4, MOV, WEBM",
                ephemeral=True
            )
            return
        media_url = fichier.url
        media_type = "video" if ext in [".mp4", ".mov", ".webm"] else "image"

    payload = {
        "username": interaction.user.display_name,
        "avatar": interaction.user.display_avatar.url,
        "text": texte or "",
        "media": media_url,
        "media_type": media_type,
    }

    try:
        async with aiohttp.ClientSession() as session:
            await session.post(SERVER_URL, json=payload, timeout=aiohttp.ClientTimeout(total=5))
        await interaction.response.send_message(
            "✅ Envoyé sur l'overlay OBS !", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erreur : `{e}`", ephemeral=True
        )

# ─────────────────────────────────────────
# /stop
# ─────────────────────────────────────────
@tree.command(
    name="stop",
    description="Arrête et cache l'overlay OBS immédiatement",
    guild=discord.Object(id=GUILD_ID)
)
async def stop_command(interaction: discord.Interaction):
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(SERVER_STOP_URL, timeout=aiohttp.ClientTimeout(total=5))
        await interaction.response.send_message(
            "⏹️ Overlay arrêté !", ephemeral=True
        )
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Erreur : `{e}`", ephemeral=True
        )

# ─────────────────────────────────────────
# /dispo
# ─────────────────────────────────────────
@tree.command(
    name="dispo",
    description="Vérifie si le serveur OBS overlay est opérationnel",
    guild=discord.Object(id=GUILD_ID)
)
async def dispo_command(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                SERVER_HEALTH_URL,
                timeout=aiohttp.ClientTimeout(total=5)
            )
            if resp.status == 200:
                await interaction.followup.send(
                    "✅ Le serveur overlay est **opérationnel** et prêt à recevoir des médias !",
                    ephemeral=True
                )
            else:
                await interaction.followup.send(
                    f"⚠️ Statut inattendu : `{resp.status}`", ephemeral=True
                )
    except aiohttp.ClientConnectionError:
        await interaction.followup.send(
            "❌ Le serveur overlay est **hors ligne**.", ephemeral=True
        )
    except aiohttp.ServerTimeoutError:
        await interaction.followup.send(
            "⏱️ Le serveur ne répond pas (timeout).", ephemeral=True
        )

# ─────────────────────────────────────────
# /obs
# ─────────────────────────────────────────
@tree.command(
    name="obs",
    description="Affiche le lien à coller dans OBS comme source navigateur",
    guild=discord.Object(id=GUILD_ID)
)
async def obs_command(interaction: discord.Interaction):
    overlay_url = f"{SERVER_PUBLIC_URL}/overlay"
    embed = discord.Embed(
        title="🖥️ Lien OBS Overlay",
        description="Colle ce lien dans une **Source Navigateur** OBS :",
        color=0x5865F2
    )
    embed.add_field(name="🔗 URL", value=f"`{overlay_url}`", inline=False)
    embed.add_field(name="📐 Résolution recommandée", value="1920 × 1080", inline=True)
    embed.add_field(name="🎨 CSS OBS", value="`body { background-color: rgba(0,0,0,0) !important; }`", inline=False)
    embed.set_footer(text="N'oublie pas de cocher 'Arrière-plan transparent' dans OBS !")
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ─────────────────────────────────────────
# Sync au démarrage
# ─────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot connecté : {client.user}")
    print(f"✅ Commandes synchronisées sur le serveur {GUILD_ID}")


client.run(DISCORD_TOKEN)
