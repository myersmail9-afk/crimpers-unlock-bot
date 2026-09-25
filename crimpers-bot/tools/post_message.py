"""Post a message to a channel, looked up by name."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

name = os.environ["CHANNEL_NAME"].lstrip("#")
channel = next((c for c in request("GET", f"/guilds/{GUILD_ID}/channels") or []
                if c["name"] == name and c.get("type") in (0, 5)), None)
if not channel:
    sys.exit(f"No text channel named #{name}")
msg = request("POST", f"/channels/{channel['id']}/messages", {"content": os.environ["MESSAGE"]})
if not msg:
    sys.exit(f"Discord refused the post - the bot may lack Send Messages in #{name}.")
print(f"posted to #{name}: msg {msg['id']}")
