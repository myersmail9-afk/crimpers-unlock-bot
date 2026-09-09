"""Always-on version: unlocks the instant someone posts an introduction."""
import os, asyncio, discord
from unlock_core import sweep, unlock_author, qualifies, INTRO_ID

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"online as {client.user}")
    # catch anyone who posted while we were down
    for name in await asyncio.to_thread(sweep):
        print(f"  caught up: {name}")


@client.event
async def on_message(message):
    if str(message.channel.id) != str(INTRO_ID):
        return
    raw = {
        "author": {"id": str(message.author.id), "bot": message.author.bot},
        "type": int(message.type.value),
        "content": message.content,
    }
    if not qualifies(raw):
        return
    if await asyncio.to_thread(unlock_author, str(message.author.id), str(message.id)):
        print(f"unlocked {message.author}")


client.run(os.environ["DISCORD_BOT_TOKEN"])
