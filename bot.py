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

# Activation/désactivation de la détection automatique (par défaut: activé)
AUTO_DETECT_ENABLED = os.getenv("AUTO_DETECT_ENABLED", "true").lower() == "true"

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Extensions autorisées
ALLOWED_EXTENSIONS = [".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mov", ".webm", ".mp3", ".wav", ".ogg"]
VIDEO_EXTENSIONS = [".mp4", ".mov", ".webm"]
AUDIO_EXTENSIONS = [".mp3", ".wav", ".ogg"]

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
# Détection automatique des messages
# ─────────────────────────────────────────
@client.event
async def on_message(message):
    # Ignorer les messages du bot lui-même
    if message.author == client.user:
        return
    
    # Ignorer les messages sans contenu
    if not message.content and not message.attachments:
        return
    
    # Vérifier s'il y a des attachments valides ou du texte
    has_valid_attachment = False
    media_url = None
    media_type = None
    
    # Traiter les attachments
    for attachment in message.attachments:
        ext = "." + attachment.filename.split(".")[-1].lower()
        if ext in ALLOWED_EXTENSIONS:
            has_valid_attachment = True
            media_url = attachment.url
            if ext in VIDEO_EXTENSIONS:
                media_type = "video"
            elif ext in AUDIO_EXTENSIONS:
                media_type = "audio"
            else:
                media_type = "image"
            break  # On prend le premier fichier valide
    
    # Si on a un attachment valide OU du texte, on envoie à l'overlay
    if has_valid_attachment or message.content.strip():
        # Vérifier si le message commence par .h
        text_content = message.content.strip() if message.content.strip() else ""
        hide_user = text_content.startswith(".h ") or text_content.startswith(".h")
        
        # Retirer le .h du texte s'il est présent
        if hide_user:
            text_content = text_content[2:].strip() if text_content.startswith(".h ") else text_content[2:]
        
        payload = {
            "username": message.author.display_name,
            "avatar": message.author.display_avatar.url,
            "text": text_content,
            "media": media_url,
            "media_type": media_type,
            "hide_user": hide_user,
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(SERVER_URL, json=payload, timeout=aiohttp.ClientTimeout(total=5))
            # Ajouter une réaction de confirmation
            try:
                await message.add_reaction("✅")
            except Exception as e:
                print(f"⚠️ Impossible d'ajouter la réaction: {e}")
        except Exception as e:
            print(f"❌ Erreur lors de l'envoi automatique: {e}")
            # Essayer d'ajouter une réaction d'erreur
            try:
                await message.add_reaction("❌")
            except:
                pass
    
    # Traiter les commandes slash (nécessaire pour les commandes)
    await client.process_commands(message)

# ─────────────────────────────────────────
# Sync au démarrage
# ─────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id=GUILD_ID))
    print(f"✅ Bot connecté : {client.user}")
    print(f"✅ Commandes synchronisées sur le serveur {GUILD_ID}")
    print(f"✅ Détection automatique des messages activée")


client.run(DISCORD_TOKEN)
