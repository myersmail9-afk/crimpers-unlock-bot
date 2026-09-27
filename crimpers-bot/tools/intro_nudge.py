"""Once a day: welcome everyone who joined since the last nudge and hasn't introduced
themselves yet, pointing them at the pinned Introduce yourself button."""
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, INTRO_ID

MARK = "Tap **👋 Introduce yourself** in the pinned post"
DRY_RUN = os.environ.get("DRY_RUN") == "true"
me = request("GET", "/users/@me")["id"]

msgs = request("GET", f"/channels/{INTRO_ID}/messages?limit=100") or []
last = next((m for m in msgs if m["author"]["id"] == me and MARK in m.get("content", "")), None)
since = (datetime.datetime.fromisoformat(last["timestamp"]) if last
         else datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
introduced = {m["author"]["id"] for m in msgs} | {
    u["id"] for m in msgs for u in m.get("mentions", [])} | {
    part[2:-1] for m in msgs for part in m.get("content", "").split() if part.startswith("<@") and part.endswith(">")}

members, after = [], "0"
while True:
    page = request("GET", f"/guilds/{GUILD_ID}/members?limit=1000&after={after}") or []
    members += page
    if len(page) < 1000:
        break
    after = page[-1]["user"]["id"]

new = [m["user"]["id"] for m in members
       if not m["user"].get("bot") and not m.get("pending")
       and datetime.datetime.fromisoformat(m["joined_at"]) > since
       and m["user"]["id"] not in introduced]
print(f"since {since.isoformat()}: {len(new)} new member(s) without an intro")
if not new:
    sys.exit(0)

text = f"Welcome {', '.join(f'<@{u}>' for u in new)}! 🤙 {MARK} to say hi. It takes 30 seconds."
if DRY_RUN:
    print("[dry run]", text)
else:
    ok = request("POST", f"/channels/{INTRO_ID}/messages",
                 {"content": text, "allowed_mentions": {"users": new[:100]}})
    print("posted:", ok is not None)
