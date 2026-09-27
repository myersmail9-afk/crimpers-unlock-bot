"""Make the intro prompt the last, required onboarding screen with clearer wording."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

TITLE = "Introduce yourself 👋"
OPTION = "I'll post my intro"
DESC = "Next, tap 👋 Introduce yourself in #introductions: a photo + a line about you, 30 sec."
assert len(DESC) <= 100, len(DESC)

ob = request("GET", f"/guilds/{GUILD_ID}/onboarding")
print("before:", json.dumps([p["title"] for p in ob["prompts"]]))

def clean(o):
    out = {k: o[k] for k in ("id", "title", "description", "role_ids", "channel_ids") if k in o}
    e = o.get("emoji") or {}
    if e.get("name"):
        out.update(emoji_id=e.get("id"), emoji_name=e["name"], emoji_animated=e.get("animated", False))
    return out

intro = [p for p in ob["prompts"] if p["title"] in ("Welcome to Crimpers!", TITLE)]
rest = [p for p in ob["prompts"] if p not in intro]
if len(intro) != 1:
    sys.exit(f"expected one intro prompt, found {len(intro)}")
p = intro[0]
p.update(title=TITLE, required=True)
p["options"][0].update(title=OPTION, description=DESC)

prompts = [{**{k: q[k] for k in ("id", "title", "single_select", "required", "in_onboarding", "type")},
            "options": [clean(o) for o in q["options"]]} for q in rest + [p]]
r = request("PUT", f"/guilds/{GUILD_ID}/onboarding", {
    "prompts": prompts, "default_channel_ids": ob["default_channel_ids"],
    "enabled": ob["enabled"], "mode": ob["mode"]})
if not r:
    sys.exit("Discord refused the onboarding update")
for n, q in enumerate(r["prompts"], 1):
    print(f"{n}. {q['title']} | required={q['required']} | {[o['title'] + ' — ' + (o.get('description') or '') for o in q['options']][:1]}")
