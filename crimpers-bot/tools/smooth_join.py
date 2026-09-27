"""Reword the rules-screening intro rule and delete invites that land in hidden channels."""
import os, sys, json, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, INTRO_ID, API, HEADERS

NEW_RULE = f"Say hi in <#{INTRO_ID}> if you want!"
HIDDEN = {"moderator-only"} | set()              # plus anything in the Archive category

# 1. rules screening - PATCH directly so a failure shows Discord's reason
mv = request("GET", f"/guilds/{GUILD_ID}/member-verification?with_guild=false")
for f in mv["form_fields"]:
    if f["field_type"] == "TERMS":
        f["values"] = [NEW_RULE if "ntroduce yourself" in v else v for v in f["values"]]
body = json.dumps({"form_fields": mv["form_fields"], "version": mv["version"], "enabled": True}).encode()
req = urllib.request.Request(f"{API}/guilds/{GUILD_ID}/member-verification", data=body, headers=HEADERS, method="PATCH")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("rules screening now:", json.loads(r.read())["form_fields"][0]["values"])
except urllib.error.HTTPError as e:
    print("rules screening update FAILED:", e.code, e.read().decode()[:300])

# 2. invites pointing at channels new people can't see
chans = request("GET", f"/guilds/{GUILD_ID}/channels") or []
archive = {c["id"] for c in chans if c["type"] == 4 and c["name"].lower() == "archive"}
hidden_ids = {c["id"] for c in chans if c["name"] in HIDDEN or c.get("parent_id") in archive}
for inv in request("GET", f"/guilds/{GUILD_ID}/invites") or []:
    ch = inv.get("channel") or {}
    if ch.get("id") in hidden_ids:
        ok = request("DELETE", f"/invites/{inv['code']}") is not None
        print(f"deleted invite to #{ch.get('name')} ({inv.get('uses')} uses):", "ok" if ok else "FAILED")
print("done")
