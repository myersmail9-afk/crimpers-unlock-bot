"""Simplify the join flow: reword the stale intro prompt, let the Logan role see
the Logan channels, and list any posts that still say intros unlock the chat."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

VIEW = 1 << 10

# 1. onboarding: reword the old "introduce yourself to unlock" prompt, make it skippable
ob = request("GET", f"/guilds/{GUILD_ID}/onboarding")
def clean(o):
    out = {k: o[k] for k in ("id", "title", "description", "role_ids", "channel_ids") if k in o}
    e = o.get("emoji") or {}
    if e.get("name"):
        out.update(emoji_id=e.get("id"), emoji_name=e["name"], emoji_animated=e.get("animated", False))
    return out
prompts = []
for p in ob["prompts"]:
    if any("unlock" in (o.get("title", "") + (o.get("description") or "")).lower() for o in p["options"]):
        p["title"] = "Welcome to Crimpers!"
        p["required"] = False
        p["options"][0]["title"] = "Got it, let's go"
        p["options"][0]["description"] = "Post anywhere, anytime. Say hi in #introductions whenever you like."
        print("rewording prompt:", p["id"])
    prompts.append({**{k: p[k] for k in ("id", "title", "single_select", "required", "in_onboarding", "type")},
                    "options": [clean(o) for o in p["options"]]})
r = request("PUT", f"/guilds/{GUILD_ID}/onboarding", {
    "prompts": prompts, "default_channel_ids": ob["default_channel_ids"],
    "enabled": ob["enabled"], "mode": ob["mode"]})
print("onboarding updated:", bool(r))
if r:
    for p in r["prompts"]:
        print("  ", p["title"], "| required", p["required"], "|", [o["title"] for o in p["options"]][:3])

# 2. Logan role can see the Logan channels
g = request("GET", f"/guilds/{GUILD_ID}")
logan = next(x["id"] for x in g["roles"] if x["name"] == "Logan")
chans = request("GET", f"/guilds/{GUILD_ID}/channels") or []
for c in chans:
    if c["name"] in ("logan-climbing", "logan-outdoors"):
        cur = next((o for o in c.get("permission_overwrites", []) if o["id"] == logan), None)
        allow = int(cur["allow"]) if cur else 0
        deny = int(cur["deny"]) if cur else 0
        ok = request("PUT", f"/channels/{c['id']}/permissions/{logan}",
                     {"type": 0, "allow": str(allow | VIEW), "deny": str(deny & ~VIEW)})
        print(f"Logan role can now view #{c['name']}:", ok is not None)

# 3. find leftover "intro unlocks the chat" wording
me = request("GET", "/users/@me")["id"]
pat = re.compile(r"unlock|introduc\w* yourself (first|before|to)|until you (introduce|post)", re.I)
for c in chans:
    if c["name"] not in ("rules", "welcome-page", "introductions", "announcements", "everyone-community-hub", "events"):
        continue
    msgs = (request("GET", f"/channels/{c['id']}/messages?limit=100") or []) + (request("GET", f"/channels/{c['id']}/pins") or [])
    seen = set()
    for m in msgs:
        if m["id"] in seen:
            continue
        seen.add(m["id"])
        text = m.get("content", "") + " ".join((e.get("description") or "") + (e.get("title") or "") for e in m.get("embeds", []))
        if pat.search(text):
            who = "BOT" if m["author"]["id"] == me else m["author"].get("username")
            print(f"\n[stale?] #{c['name']} msg {m['id']} by {who} pinned={m.get('pinned')}\n{text[:600]}")
print("done")
