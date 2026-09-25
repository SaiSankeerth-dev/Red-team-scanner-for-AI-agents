# CTF target APIs — investigation results

**Date:** 2026-09-26
**Method:** page-source/JS analysis + gentle curl verification (one benign "hello" per verified target).
**Status:** 2 of 6 chat APIs verified working. Nothing attacked; only "hello"-style messages sent.

---

## 1. Lakera Gandalf — ✅ VERIFIED

Multi-level password-guessing game. The classic REST API still works.

- **Method + URL:** `POST https://gandalf-api.lakera.ai/api/send-message`
- **Body:** `application/x-www-form-urlencoded` — `defender=<level>&prompt=<message>`
- **Levels (`defender`):** `baseline`, `do-not-tell`, `do-not-tell-and-block`,
  `gpt-is-password-encoded`, `word-blacklist`, `gpt-blacklist`, `gandalf`,
  `gandalf-the-white`, `adventure-1`, `adventure-2`
- **Reply field:** `answer`
- **Headers:** a browser-like `User-Agent` is REQUIRED — without it the host
  returns nginx `503`. No cookies/auth needed.
- **Password check:** same endpoint, body `defender=<level>&password=<guess>` →
  `{"success": true|false, ...}`
- **Rate limiting:** none observed on single requests. PyRIT's GandalfTarget
  supports `max_requests_per_minute`; stay ≤ ~10/min to be polite.

### Verified example

Request:
```bash
curl -s -X POST "https://gandalf-api.lakera.ai/api/send-message" \
  -A "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36" \
  --data-urlencode "defender=baseline" \
  --data-urlencode "prompt=hello"
```

Response (`200`):
```json
{"answer":"Hello! How can I assist you today?","defender":"baseline","prompt":"hello"}
```

### Adapter notes for Redline
Trivial REST adapter: POST form fields, read `answer`. Stateless per request
(one-turn). Level maps to Redline "target variant".

---

## 2. TensorTrust — ❌ NOT CURL-FEASIBLE (account + captcha wall)

Stanford/Berkeley prompt-hacking game (open source:
`HumanCompatibleAI/tensor-trust`, Django backend).

- Attacks are **not** a simple chat endpoint: you attack *other players'*
  LLM defenses via matchmaking, and responses stream back as
  `text/event-stream` (SSE).
- **Everything requires an authenticated account.** Signup goes through
  `POST /authenticate` with **reCAPTCHA**. Even the tutorial
  (`POST /tutorial/<step>/submit.php`, form field `attacker_input`) rejects
  unauthenticated users.
- Relevant server routes (from source): `ajax/security_submit`,
  `ajax/attack_table`, `ajax/unlock_account`, `create_flag`.
- Rate limiting/cooldowns are built into the game (`cooldown.py`,
  `rate_limiting.py`).

**Verdict:** automated probing needs a real account created through the
captcha — not feasible via curl. Defer to a browser-driven flow or drop
from adapter v1.

---

## 3. Prompt Airlines (Wiz CTF) — ✅ VERIFIED

Airline customer-service chatbot CTF.

- **Step 1 — session:** `GET https://promptairlines.com/` (stores a session cookie)
- **Step 2 — chat:** `POST https://promptairlines.com/chat`
  - Body: JSON `{"prompt": "<message>"}`, `Content-Type: application/json`
  - Send the session cookie jar
- **Reply field:** `content` (HTML string, e.g. `<p>Hello! ...</p>`)
- **Optional auth:** `User-Id-Token: Bearer <firebase-id-token>` header unlocks
  member features (via ticket upload / Google sign-in). **Not needed** for
  basic chat.
- **Other endpoints:** `GET /challenge` (challenge state),
  `POST /submit_flag` with `{"flag": "..."}`.
- **Rate limiting:** none observed; keep human-like cadence.

### Verified example

Request:
```bash
curl -s -c cookies.txt -b cookies.txt -X POST "https://promptairlines.com/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"hello"}'
```

Response (`200`, truncated):
```json
{"type": "message", "content": "<p>Hello! Nice to hear from you. How can I assist you today?</p>\n<p>I can help with:\n- Searching for flights\n- Viewing your existing tickets\n- Booking a flight (via our secure process)</p>..."}
```

### Adapter notes for Redline
Cookie jar + POST JSON, strip HTML from `content`. Note the bot resets the
conversation if it repeats a response — the adapter should treat that as
a normal turn, not an error.

---

## 4. Doublespeak — ❌ BACKEND CURRENTLY DOWN

AI escape game by Forces Unseen ("discover the bot's name").

Routes recovered from the frontend bundle (`/assets/index.js`):
- `POST /api/chat` — body `{"message": "..."}`, session-cookie auth (401 → login)
- `POST /api/register` — body
  `{"email","username","password","legal","subscribe"}` (201 on success)
- `GET /api/player`, `GET /api/leaders`, `POST /api/flag {"flag"}`,
  `POST /api/playground {"temperature","messages"}`, `POST /api/reset`

**Problem:** as of 2026-09-26 every `/api/*` path on `https://doublespeak.chat`
returns nginx `404`, and `api.`/`www.` subdomains don't resolve. The frontend
loads fine, so the backend is down or moved.

**Verdict:** unverifiable right now. Re-check later; if the API returns, the
adapter is: register once → cookie jar → `POST /api/chat`.

---

## 5. Prompt Injection CTF 2026 — ⚠️ PARTIAL (stats API works; chat is server actions)

16-level Next.js app on Firebase Hosting (`prompt-injection-ctf-2026.web.app`).

- **Working:** `GET https://prompt-injection-ctf-2026.web.app/api/stats/global`
  → `200` with JSON like
  `{"totalPlayers":39,"totalSolves":125,"recentActivity":[...], ...}`.
- **Chat:** there is **no plain REST chat endpoint**. The app submits attacks
  through **Next.js server actions** (`Next-Action` protocol), not fetchable
  REST routes — `/api/chat`, `/api/level`, `/api/submit` all `404`.
- Driving chat via curl would require extracting the RSC server-action ID
  per page load — fragile.

**Verdict:** stats endpoint documented; chat needs browser automation
(Playwright) or server-action reverse engineering. Defer to adapter v2.

---

## 6. PortSwigger Web Security Academy LLM labs — 📝 DOCUMENTED (no account created)

8 deliberately vulnerable labs under `https://portswigger.net/web-security/llm-attacks/`:

| # | Lab | Level |
|---|---|---|
| 1 | Exploiting LLM APIs with excessive agency | Apprentice |
| 2 | Exploiting vulnerabilities in LLM APIs | Practitioner |
| 3 | Indirect prompt injection | Practitioner |
| 4 | Exploiting insecure output handling in LLMs | Expert |
| 5 | Exploiting AI agents to trigger secondary vulnerabilities | Practitioner |
| 6 | Exploiting AI agents to perform destructive actions | Apprentice |
| 7 | Exploiting AI agents to exfiltrate sensitive information | Apprentice |
| 8 | Bypassing AI scanner defenses to exfiltrate sensitive information | Practitioner |

Lab URLs follow the pattern:
`https://portswigger.net/web-security/llm-attacks/lab-<slug>`
(e.g. `/lab-exploiting-llm-apis-with-excessive-agency`).

### How a lab is launched (documented, not performed)
1. Create a **free** PortSwigger account (not done — per task constraints).
2. Open the lab page, click **"Access the lab"**.
3. Academy spins up a **per-user lab instance** at a unique, temporary URL
   (pattern `https://<random-id>.web-security-academy.net/`), valid for the
   session.
4. The lab page shows the objective plus a **"Live chat"** button; the chat
   widget talks to the lab instance's backend (instance-scoped, discovered
   at runtime — no static API to document).
5. Example (Lab 1): ask the LLM what APIs it has → it exposes a Debug SQL
   API → ask it to call `DELETE FROM users WHERE username='carlos'` → solved.

### Adapter notes for Redline
No static API exists — the adapter must: launch the lab in an authenticated
session, capture the instance URL, and drive the instance's chat widget.
This is inherently browser-driven (also needs the PortSwigger account).
Defer until browser automation is available; highest-value labs for Redline
are #1 (excessive agency), #3 (indirect injection), #5/#7 (agentic attacks).

---

## Summary for adapter planning

| Target | Status | Adapter path |
|---|---|---|
| Gandalf | ✅ verified | trivial REST (form POST) |
| PromptAirlines | ✅ verified | cookie session + JSON POST |
| TensorTrust | ❌ account+captcha wall | browser flow or skip |
| Doublespeak | ❌ backend down | retry later; routes known |
| CTF 2026 | ⚠️ server actions only | browser automation |
| PortSwigger labs | 📝 per-user instances | browser + Academy account |

**Recommendation:** build the Redline `http` target adapter against Gandalf
and PromptAirlines first (both verified above with exact request/response
shapes). The other four need browser automation or account flows.
