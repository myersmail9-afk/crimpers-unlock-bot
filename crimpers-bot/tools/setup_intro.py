"""Wire up the intro form: point Discord at the Worker, add the button to the
pinned #introductions post, and tell people about it in onboarding."""
import os, sys, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, INTRO_ID, API, HEADERS

WORKER_URL = os.environ["WORKER_URL"]
PINNED_ID = "1547330677362393229"

# 1. interactions endpoint (Discord pings the Worker to verify it before saving)
req = urllib.request.Request(f"{API}/applications/@me", method="PATCH", headers=HEADERS,
                             data=json.dumps({"interactions_endpoint_url": WORKER_URL}).encode())
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("interactions endpoint:", json.loads(r.read()).get("interactions_endpoint_url"))
except urllib.error.HTTPError as e:
    sys.exit(f"endpoint FAILED {e.code}: {e.read().decode()[:400]}")

# 2. pinned intro post gets the button
text = (
    "👋 **Welcome to Crimpers 2.0 — introduce yourself!**\n\n"
    "Tap the button below. It takes 30 seconds: your name, what you're into, and a photo.\n"
    "We ask for a photo so we know new members are real people who are serious about getting out with the crew. "
    "Your intro gets posted right here.\n\n"
    "You can already post anywhere in the server. See you out there. 🤙"
)
button = [{"type": 1, "components": [
    {"type": 2, "style": 1, "label": "Introduce yourself", "emoji": {"name": "👋"}, "custom_id": "intro:open"}]}]
msg = request("PATCH", f"/channels/{INTRO_ID}/messages/{PINNED_ID}", {"content": text, "components": button})
print("pinned post updated:", msg is not None)

# 3. onboarding welcome points at the intro
ob = request("GET", f"/guilds/{GUILD_ID}/onboarding")
def clean(o):
    out = {k: o[k] for k in ("id", "title", "description", "role_ids", "channel_ids") if k in o}
    e = o.get("emoji") or {}
    if e.get("name"):
        out.update(emoji_id=e.get("id"), emoji_name=e["name"], emoji_animated=e.get("animated", False))
    return out
for p in ob["prompts"]:
    if p["title"] == "Welcome to Crimpers!":
        p["options"][0]["title"] = "Got it, let's go"
        p["options"][0]["description"] = "Next: introduce yourself with a photo in #introductions (30 seconds)."
        p["options"][0]["channel_ids"] = [INTRO_ID]
r = request("PUT", f"/guilds/{GUILD_ID}/onboarding", {
    "prompts": [{**{k: p[k] for k in ("id", "title", "single_select", "required", "in_onboarding", "type")},
                 "options": [clean(o) for o in p["options"]]} for p in ob["prompts"]],
    "default_channel_ids": ob["default_channel_ids"], "enabled": ob["enabled"], "mode": ob["mode"]})
print("onboarding updated:", bool(r))
