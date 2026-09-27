"""Report how access is gated: roles, channel overwrites, join settings, invites."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, MEMBER_ID

BITS = {"view": 1 << 10, "send": 1 << 11, "history": 1 << 16, "react": 1 << 6,
        "attach": 1 << 15, "connect": 1 << 20, "invite": 1 << 0, "threads": 1 << 38,
        "admin": 1 << 3, "manage_roles": 1 << 28, "manage_guild": 1 << 5, "manage_channels": 1 << 4}

def flags(p):
    p = int(p)
    return ",".join(k for k, b in BITS.items() if p & b) or "-"

g = request("GET", f"/guilds/{GUILD_ID}?with_counts=true")
print("guild:", g["name"], "| members ~", g.get("approximate_member_count"))
print("verification_level:", g["verification_level"], "| mfa:", g["mfa_level"],
      "| explicit_filter:", g["explicit_content_filter"])
print("features:", ", ".join(sorted(g.get("features", []))))
print("rules_channel:", g.get("rules_channel_id"), "| system_channel:", g.get("system_channel_id"))

print("\n=== roles (position, name, perms) ===")
roles = sorted(g["roles"], key=lambda r: -r["position"])
for r in roles:
    tag = " <-- MEMBER" if r["id"] == MEMBER_ID else (" <-- @everyone" if r["id"] == GUILD_ID else "")
    print(r["position"], r["name"], flags(r["permissions"]), "| bot-managed" if r.get("managed") else "", tag)

me = request("GET", "/users/@me")
print("\nbot user:", me["username"], me["id"])

print("\n=== channels + overwrites for @everyone / Member ===")
chans = request("GET", f"/guilds/{GUILD_ID}/channels") or []
cats = {c["id"]: c["name"] for c in chans if c["type"] == 4}
for c in sorted(chans, key=lambda c: (c.get("parent_id") or c["id"], c["type"] != 4, c["position"])):
    ow = []
    for o in c.get("permission_overwrites", []):
        who = "@everyone" if o["id"] == GUILD_ID else ("Member" if o["id"] == MEMBER_ID else
              next((r["name"] for r in roles if r["id"] == o["id"]), f"user:{o['id']}"))
        ow.append(f"{who}[+{flags(o['allow'])} / -{flags(o['deny'])}]")
    kind = {0: "#", 2: "🔊", 4: "CAT", 5: "📢", 15: "forum", 13: "stage"}.get(c["type"], c["type"])
    print(f"{kind} {c['name']} (in {cats.get(c.get('parent_id'), '-')}) synced={c.get('parent_id') is not None} :: {'; '.join(ow) or 'no overwrites'}")

print("\n=== member verification / rules screening ===")
print(json.dumps(request("GET", f"/guilds/{GUILD_ID}/member-verification?with_guild=false"), indent=1)[:1500])
print("\n=== onboarding ===")
ob = request("GET", f"/guilds/{GUILD_ID}/onboarding")
if ob:
    print("enabled:", ob.get("enabled"), "mode:", ob.get("mode"), "default_channels:", len(ob.get("default_channel_ids", [])), "prompts:", len(ob.get("prompts", [])))
print("\n=== invites ===")
inv = request("GET", f"/guilds/{GUILD_ID}/invites")
if inv is None:
    print("(no access to invites)")
for i in inv or []:
    print(i["code"], "| channel #", (i.get("channel") or {}).get("name"), "| uses", i.get("uses"), "/", i.get("max_uses") or "∞",
          "| max_age", i.get("max_age"), "| expires", i.get("expires_at"), "| temporary", i.get("temporary"),
          "| by", (i.get("inviter") or {}).get("username"))
print("\nvanity:", request("GET", f"/guilds/{GUILD_ID}/vanity-url"))
