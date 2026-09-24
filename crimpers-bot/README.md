# Crimpers 2.0 — intro unlock bot

Grants the **Member** role to anyone who posts an introduction in `#introductions`,
which is what unlocks posting everywhere else in the server.

There are two ways to run it. Both use the same logic (`unlock_core.py`).

## Option A — GitHub Actions (free, no server)

Runs on GitHub's machines on a schedule. Nothing to host, nothing to pay for.
Unlocks land within roughly 5–15 minutes of someone posting.

1. Create a new repository and upload these files.
2. Settings → Secrets and variables → Actions:
   - **Secrets** tab → New secret → `DISCORD_BOT_TOKEN` = the bot token
   - **Variables** tab → add `GUILD_ID`, `INTRO_CHANNEL_ID`, `MEMBER_ROLE_ID` (values in `IDS.txt`)
3. Actions tab → enable workflows. It now runs every 10 minutes.
   You can also hit "Run workflow" to unlock someone immediately.

### Make the repo public

GitHub Actions minutes are **unlimited on public repos**, but a free private repo
only gets 2,000 minutes a month — and a 10-minute schedule burns roughly twice that.
Nothing secret lives in this code (the token is stored as an encrypted Actions
secret, not in the files), so public is the simple answer.

If you'd rather keep it private, open `.github/workflows/unlock.yml` and change
`*/10` to `*/30`. That stays inside the free allowance.

## Option B — always on (instant)

Any host that runs a container or a Python process: `python bot.py`,
or build the included `Dockerfile`. Set the same four environment variables.
This unlocks the moment someone posts, and sweeps for anyone missed on startup.

## Settings

| Variable | Meaning |
|---|---|
| `MIN_INTRO_CHARS` | Minimum characters to count as a real intro (default 10, stops "hi" from unlocking) |

## Safety

- Only ever **adds** the Member role. It never removes roles, kicks, bans, or deletes.
- Skips bots and system messages.
- Reacts ✅ to the intro so the newcomer gets confirmation.
- Idempotent: re-running it changes nothing for people already unlocked.
