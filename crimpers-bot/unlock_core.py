"""Shared logic: grant the Member role to anyone who has posted an intro."""
import os, time, json, urllib.request, urllib.error

API = "https://discord.com/api/v10"
TOKEN     = os.environ["DISCORD_BOT_TOKEN"]
GUILD_ID  = os.environ["GUILD_ID"]
INTRO_ID  = os.environ["INTRO_CHANNEL_ID"]
MEMBER_ID = os.environ["MEMBER_ROLE_ID"]
MIN_CHARS = int(os.environ.get("MIN_INTRO_CHARS", "10"))

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "User-Agent": "CrimpersUnlockBot (https://github.com/, 1.0)",
    "Content-Type": "application/json",
}


def request(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, headers=HEADERS, method=method)
    for _ in range(6):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 429:                      # rate limited - wait it out
                time.sleep(float(json.load(e).get("retry_after", 1)) + 0.4)
                continue
            if e.code in (403, 404):               # member left, or missing perms
                return None
            raise
    return None


def qualifies(msg):
    """A real introduction: a human, with actual content."""
    if msg.get("author", {}).get("bot"):
        return False
    if msg.get("type") not in (0, 19):             # normal message or reply
        return False
    return len(msg.get("content", "").strip()) >= MIN_CHARS


def unlock_author(user_id, message_id=None):
    """Grant Member. Returns True if this actually changed something."""
    member = request("GET", f"/guilds/{GUILD_ID}/members/{user_id}")
    if member is None:
        return False
    if MEMBER_ID in member.get("roles", []):
        return False
    request("PUT", f"/guilds/{GUILD_ID}/members/{user_id}/roles/{MEMBER_ID}")
    if message_id:                                  # visible confirmation for the newcomer
        request("PUT", f"/channels/{INTRO_ID}/messages/{message_id}/reactions/%E2%9C%85/@me")
    return True


def sweep(limit=100):
    """Catch up on anyone who posted while the bot was not listening."""
    msgs = request("GET", f"/channels/{INTRO_ID}/messages?limit={limit}") or []
    seen, unlocked = set(), []
    for m in msgs:
        uid = m.get("author", {}).get("id")
        if not uid or uid in seen or not qualifies(m):
            continue
        seen.add(uid)
        if unlock_author(uid, m["id"]):
            unlocked.append(m["author"].get("username", uid))
        time.sleep(0.3)
    return unlocked
