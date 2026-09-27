// Crimpers intro form: "Introduce yourself" button -> pop-up form (name, blurb, photo)
// -> posted to #introductions as the member, via a channel webhook.
const API = "https://discord.com/api/v10";
const WEBHOOK_NAME = "Crimpers Intros";

export default {
  async fetch(req, env, ctx) {
    if (req.method !== "POST") return new Response("Crimpers intro bot is running.");

    const sig = req.headers.get("x-signature-ed25519");
    const ts = req.headers.get("x-signature-timestamp");
    const body = await req.text();
    if (!sig || !ts || !(await verify(env.DISCORD_PUBLIC_KEY, sig, ts + body))) {
      return new Response("invalid request signature", { status: 401 });
    }

    const i = JSON.parse(body);
    if (i.type === 1) return json({ type: 1 });                                  // PING
    if (i.type === 3 && i.data.custom_id === "intro:open") {
      return json({ type: 9, data: introForm() });                               // open modal
    }
    if (i.type === 5 && i.data.custom_id === "intro:submit") {
      ctx.waitUntil(postIntro(i, env).catch((e) =>
        reply(i, `Couldn't post your intro (${e.message}). Give it another try in a minute.`)));
      return json({ type: 5, data: { flags: 64 } });                             // "thinking...", only they see it
    }
    return json({ type: 4, data: { content: "That button isn't wired up.", flags: 64 } });
  },
};

function introForm() {
  return {
    custom_id: "intro:submit",
    title: "Introduce yourself 👋",
    components: [
      { type: 10, content:
        "We ask for a quick intro and a photo so we know new members are real people who are " +
        "serious about getting out with the crew. It posts to #introductions." },
      { type: 18, label: "What should we call you?",
        component: { type: 4, custom_id: "name", style: 1, min_length: 1, max_length: 60, required: true } },
      { type: 18, label: "What are you into?",
        description: "Where you climb, what else you do outside, what you're looking for",
        component: { type: 4, custom_id: "about", style: 2, min_length: 10, max_length: 800, required: true,
                     placeholder: "Mostly bouldering at ARC, trying to get outside more. Also trail running." } },
      { type: 18, label: "A photo of you",
        description: "Climbing, outside, or just your face. Anything real.",
        component: { type: 19, custom_id: "photo", min_values: 1, max_values: 1, required: true } },
    ],
  };
}

async function postIntro(i, env) {
  const fields = {};
  (function walk(n) {
    if (Array.isArray(n)) return n.forEach(walk);
    if (!n || typeof n !== "object") return;
    if (n.custom_id) fields[n.custom_id] = n.value ?? n.values;
    walk(n.component); walk(n.components);
  })(i.data.components);

  const name = String(fields.name || "").trim();
  const about = String(fields.about || "").trim();
  const photo = i.data.resolved?.attachments?.[(fields.photo || [])[0]];
  if (!photo) return reply(i, "Please add a photo. It's how we know new members are real people.");
  if (!(photo.content_type || "").startsWith("image/")) {
    return reply(i, "That file isn't an image. Tap the button again and pick a photo.");
  }

  const user = i.member.user;
  const img = await fetch(photo.url);
  if (!img.ok) throw new Error("photo download failed");

  const hook = await introWebhook(env);
  const form = new FormData();
  form.append("payload_json", JSON.stringify({
    username: webhookName(name, user.username),
    avatar_url: avatarUrl(i.member, env.GUILD_ID),
    content: `**${name}** · <@${user.id}>\n${about}`,
    allowed_mentions: { parse: [] },
    attachments: [{ id: 0, filename: photo.filename }],
  }));
  form.append("files[0]", await img.blob(), photo.filename);
  const res = await fetch(`${API}/webhooks/${hook.id}/${hook.token}?wait=true`, { method: "POST", body: form });
  if (!res.ok) throw new Error(`post failed ${res.status}`);
  const msg = await res.json();

  await bot(env, "PUT", `/channels/${env.INTRO_CHANNEL_ID}/messages/${msg.id}/reactions/%F0%9F%91%8B/@me`);
  await reply(i, `You're introduced! 🎉 https://discord.com/channels/${env.GUILD_ID}/${env.INTRO_CHANNEL_ID}/${msg.id}`);
}

let cachedHook;
async function introWebhook(env) {
  if (cachedHook) return cachedHook;
  const hooks = await bot(env, "GET", `/channels/${env.INTRO_CHANNEL_ID}/webhooks`);
  cachedHook = hooks.find((h) => h.name === WEBHOOK_NAME && h.token)
    || await bot(env, "POST", `/channels/${env.INTRO_CHANNEL_ID}/webhooks`, { name: WEBHOOK_NAME });
  return cachedHook;
}

// Webhook names can't contain "discord" or "clyde" and max out at 80 chars.
function webhookName(name, fallback) {
  const n = name.replace(/discord|clyde/gi, "").trim().slice(0, 80);
  return n || fallback;
}

function avatarUrl(member, guildId) {
  const u = member.user;
  if (member.avatar) return `https://cdn.discordapp.com/guilds/${guildId}/users/${u.id}/avatars/${member.avatar}.png`;
  if (u.avatar) return `https://cdn.discordapp.com/avatars/${u.id}/${u.avatar}.png`;
  return `https://cdn.discordapp.com/embed/avatars/${Number((BigInt(u.id) >> 22n) % 6n)}.png`;
}

async function bot(env, method, path, body) {
  const res = await fetch(API + path, {
    method,
    headers: { Authorization: `Bot ${env.DISCORD_BOT_TOKEN}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`${method} ${path.split("/")[1]} ${res.status}`);
  return res.status === 204 ? null : res.json();
}

// Replace the private "thinking..." message the member sees.
function reply(i, content) {
  return fetch(`${API}/webhooks/${i.application_id}/${i.token}/messages/@original`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
}

async function verify(publicKey, sig, message) {
  const hex = (h) => new Uint8Array(h.match(/.{2}/g).map((b) => parseInt(b, 16)));
  const key = await crypto.subtle.importKey("raw", hex(publicKey), { name: "Ed25519" }, false, ["verify"]);
  return crypto.subtle.verify("Ed25519", key, hex(sig), new TextEncoder().encode(message));
}

const json = (obj) => new Response(JSON.stringify(obj), { headers: { "Content-Type": "application/json" } });
