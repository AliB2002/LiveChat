import discord
import asyncio
import os

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print("🧹 Suppression des commandes globales...")
    await tree.sync()

    print(f"🧹 Suppression des commandes du guild {GUILD_ID}...")
    tree.clear_commands(guild=discord.Object(id=GUILD_ID))
    await tree.sync(guild=discord.Object(id=GUILD_ID))

    print("✅ Toutes les commandes supprimées !")
    await client.close()

client.run(DISCORD_TOKEN)
