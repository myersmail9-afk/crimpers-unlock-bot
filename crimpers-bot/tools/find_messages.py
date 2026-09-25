"""Print recent messages from one author across the server (manual lookup tool)."""
import os, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID

AUTHOR = os.environ.get("AUTHOR", "").lower()
DAYS = int(os.environ.get("DAYS", "14"))
cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DAYS)

channels = request("GET", f"/guilds/{GUILD_ID}/channels") or []
names = {c["id"]: c["name"] for c in channels}
blank = total = 0
for c in channels:
    if c.get("type") not in (0, 5):                 # text + announcement channels
        continue
    msgs = request("GET", f"/channels/{c['id']}/messages?limit=100")
    if msgs is None:
        print(f"[no access] #{c['name']}")
        continue
    for m in msgs:
        total += 1
        if not m.get("content"):
            blank += 1
        a = m.get("author", {})
        who = f"{a.get('username','')} {a.get('global_name') or ''}".lower()
        ts = datetime.datetime.fromisoformat(m["timestamp"])
        if AUTHOR in who and ts >= cutoff:
            print(f"--- #{c['name']} | {m['timestamp']} | {a.get('global_name') or a.get('username')} | msg {m['id']}")
            print(m.get("content") or "(no text)")
            for e in m.get("embeds", []):
                print("  [embed]", e.get("title"), e.get("description"))
            for att in m.get("attachments", []):
                print("  [attachment]", att.get("filename"))

print(f"\nscanned {total} messages, {blank} had blank content")

print("\n=== existing scheduled events ===")
for ev in request("GET", f"/guilds/{GUILD_ID}/scheduled-events") or []:
    print(ev["id"], ev["name"], ev["scheduled_start_time"], (ev.get("entity_metadata") or {}).get("location"))
