"""Edit the pinned welcome posts so intros read as optional (posting is open to everyone)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from unlock_core import request, GUILD_ID, INTRO_ID

I = f"<#{INTRO_ID}>"
EDITS = {
    "welcome-page": ("1547330691400859678", [
        (f"1. Post an introduction in {I}. That unlocks posting everywhere else.",
         f"1. Jump in anywhere, you can post right away. Say hi in {I} if you like!"),
    ]),
    "introductions": ("1547330677362393229", [
        ("post an intro here and the rest of the server unlocks.", "say hi here!"),
        ("Once you post, you'll be able to talk everywhere else. See you out there.",
         "Totally optional, you can already post anywhere in the server. See you out there."),
    ]),
}
chans = {c["name"]: c["id"] for c in request("GET", f"/guilds/{GUILD_ID}/channels") or []}
for name, (mid, reps) in EDITS.items():
    msg = request("GET", f"/channels/{chans[name]}/messages/{mid}")
    text = msg["content"]
    for old, new in reps:
        if old not in text:
            sys.exit(f"#{name}: expected text not found: {old!r}")
        text = text.replace(old, new)
    ok = request("PATCH", f"/channels/{chans[name]}/messages/{mid}", {"content": text})
    print(f"#{name} edited: {ok is not None}\n{text}\n")
