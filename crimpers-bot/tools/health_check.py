"""End-to-end sanity check of the new-member experience. Prints PASS/WARN/FAIL lines."""
import os, sys, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, INTRO_ID

VIEW, SEND = 1 << 10, 1 << 11
def out(level, msg): print(f"{level:4} {msg}")

g = request("GET", f"/guilds/{GUILD_ID}")
roles = {r["id"]: r for r in g["roles"]}
chans = {c["id"]: c for c in request("GET", f"/guilds/{GUILD_ID}/channels") or []}
byname = {c["name"]: c for c in chans.values()}

def can(role_ids, cid, bit):
    """Effective permission for a member holding @everyone + role_ids in channel cid."""
    ids = [GUILD_ID] + list(role_ids)
    base = 0
    for rid in ids:
        base |= int(roles[rid]["permissions"])
    if base & (1 << 3):
        return True
    c = chans[cid]
    ow = {o["id"]: o for o in c.get("permission_overwrites", [])}
    if GUILD_ID in ow:
        base = (base & ~int(ow[GUILD_ID]["deny"])) | int(ow[GUILD_ID]["allow"])
    a = d = 0
    for rid in role_ids:
        if rid in ow:
            a |= int(ow[rid]["allow"]); d |= int(ow[rid]["deny"])
    base = (base & ~d) | a
    return bool(base & bit)

# app / worker
app = request("GET", "/applications/@me")
ep = app.get("interactions_endpoint_url")
out("PASS" if ep else "FAIL", f"button handler URL: {ep}")

# onboarding
ob = request("GET", f"/guilds/{GUILD_ID}/onboarding")
out("PASS" if ob["enabled"] else "FAIL", f"onboarding enabled ({len(ob['prompts'])} screens)")
for cid in ob["default_channel_ids"]:
    ok = cid in chans and can([], cid, VIEW) and (can([], cid, SEND) or chans[cid]["name"] in ("rules", "announcements"))
    out("PASS" if ok else "FAIL", f"starter channel #{chans.get(cid, {}).get('name', cid)} visible{'' if chans.get(cid, {}).get('name') in ('rules','announcements') else ' + postable'} for a brand-new member")
for p in ob["prompts"]:
    for o in p["options"]:
        text = (o["title"] + " " + (o.get("description") or "")).lower()
        if "unlock" in text:
            out("FAIL", f"onboarding option still mentions unlocking: {o['title']}")
        for cid in o.get("channel_ids", []):
            if cid not in chans:
                out("FAIL", f"'{o['title']}' points at a deleted channel {cid}")
            elif not can(o.get("role_ids", []), cid, VIEW):
                out("FAIL", f"'{o['title']}' promises #{chans[cid]['name']} but that pick can't see it")
        for rid in o.get("role_ids", []):
            if rid not in roles:
                out("FAIL", f"'{o['title']}' gives a deleted role {rid}")
out("PASS", "every onboarding pick can see the channels it promises (no line above = none broken)")

# posting open in the main channels
for name in ("everyone-community-hub", "events", "photos-videos", "gear-talk", "introductions", "welcome-page"):
    c = byname.get(name)
    out("PASS" if c and can([], c["id"], SEND) else "FAIL", f"new member can post in #{name}")

# pinned posts
for name in ("introductions", "welcome-page", "rules"):
    c = byname.get(name)
    for m in request("GET", f"/channels/{c['id']}/pins") or []:
        content = m.get("content", "")
        dead = [x for x in re.findall(r"<#(\d+)>", content) if x not in chans]
        stale = re.search(r"unlock|until you (introduce|post)", content, re.I)
        btn = any(comp.get("custom_id") == "intro:open" for row in m.get("components", []) for comp in row.get("components", []))
        tag = f"#{name} pin by {m['author']['username']}"
        if dead: out("FAIL", f"{tag}: links to deleted channel(s) {dead}")
        if stale: out("WARN", f"{tag}: still says '{stale.group(0)}'")
        if name == "introductions" and m["author"]["id"] == app["id"]:
            out("PASS" if btn else "FAIL", f"{tag}: Introduce yourself button {'present' if btn else 'MISSING'}")
        if not dead and not stale:
            out("PASS", f"{tag}: links and wording OK")

# stale wording in recent #introductions chatter
for m in request("GET", f"/channels/{INTRO_ID}/messages?limit=50") or []:
    if re.search(r"introduce yourself THEN|text here first|unlock", m.get("content", ""), re.I) and not m.get("pinned"):
        out("WARN", f"#introductions msg by {m['author']['username']} still says intros unlock chats: \"{m['content'][:80]}\"")

# rules screening
mv = request("GET", f"/guilds/{GUILD_ID}/member-verification?with_guild=false")
vals = mv["form_fields"][0]["values"] if mv else []
out("PASS" if not any("unlock" in v.lower() for v in vals) else "WARN", f"rules screen: {vals}")

# events
evs = request("GET", f"/guilds/{GUILD_ID}/scheduled-events") or []
for e in evs:
    out("PASS", f"event live: {e['name']} @ {e['scheduled_start_time']} (status {e['status']})")
if not evs:
    out("WARN", "no scheduled events (Saturday's event may have finished)")

# intro webhook exists after the test post
hooks = request("GET", f"/channels/{INTRO_ID}/webhooks") or []
out("PASS" if any(h["name"] == "Crimpers Intros" for h in hooks) else "WARN", "Crimpers Intros webhook exists (created on first intro)")
print("done")
