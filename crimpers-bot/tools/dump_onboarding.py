"""Print the full new-member flow config as JSON (onboarding, welcome screen, rules screening)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

g = request("GET", f"/guilds/{GUILD_ID}")
chans = request("GET", f"/guilds/{GUILD_ID}/channels") or []
print(json.dumps({
    "guild": {k: g.get(k) for k in ("name", "description", "verification_level", "rules_channel_id", "features")},
    "roles": {r["id"]: r["name"] for r in g["roles"]},
    "channels": {c["id"]: {"name": c["name"], "type": c["type"], "parent": c.get("parent_id")} for c in chans},
    "onboarding": request("GET", f"/guilds/{GUILD_ID}/onboarding"),
    "welcome_screen": request("GET", f"/guilds/{GUILD_ID}/welcome-screen"),
    "member_verification": request("GET", f"/guilds/{GUILD_ID}/member-verification?with_guild=false"),
}))
