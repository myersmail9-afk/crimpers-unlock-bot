"""Create an in-person (external) scheduled event in the server."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

event = request("POST", f"/guilds/{GUILD_ID}/scheduled-events", {
    "name": os.environ["EVENT_NAME"],
    "description": os.environ.get("EVENT_DESCRIPTION", ""),
    "scheduled_start_time": os.environ["EVENT_START"],   # ISO 8601, UTC
    "scheduled_end_time": os.environ["EVENT_END"],
    "entity_type": 3,                                    # external / in person
    "entity_metadata": {"location": os.environ["EVENT_LOCATION"]},
    "privacy_level": 2,                                  # guild only
})
if not event:
    sys.exit("Discord refused the request - the bot likely needs the Manage Events permission.")
print(f"created: {event['name']} ({event['id']})")
print(f"https://discord.com/events/{GUILD_ID}/{event['id']}")
