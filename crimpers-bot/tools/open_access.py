"""Let @everyone post wherever the Member role used to unlock posting.

For each channel where Member's overwrite allows a permission that @everyone's
overwrite denies, drop that deny. View-gating (role-only channels) is untouched.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, MEMBER_ID

DRY_RUN = os.environ.get("DRY_RUN", "true") == "true"

for c in request("GET", f"/guilds/{GUILD_ID}/channels") or []:
    ow = {o["id"]: o for o in c.get("permission_overwrites", [])}
    everyone, member = ow.get(GUILD_ID), ow.get(MEMBER_ID)
    if not everyone or not member:
        continue
    lift = int(everyone["deny"]) & int(member["allow"])
    if not lift:
        continue
    new_deny = int(everyone["deny"]) & ~lift
    print(f"{'[dry run] ' if DRY_RUN else ''}#{c['name']}: @everyone deny {everyone['deny']} -> {new_deny}")
    if not DRY_RUN:
        r = request("PUT", f"/channels/{c['id']}/permissions/{GUILD_ID}",
                    {"type": 0, "allow": everyone["allow"], "deny": str(new_deny)})
        if r is None:
            sys.exit(f"failed on #{c['name']}")
print("done")
