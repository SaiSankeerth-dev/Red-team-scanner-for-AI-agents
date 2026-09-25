# Redline — Public Demo Targets Research

**Date:** 2026-09-26
**Status:** Research only. No emails sent. No scans run.
**Rule:** Nothing in this file is an authorization to scan. Bucket A entries may only be probed within the challenge's intended behavior (chat-based attack prompts at human-like rates). Bucket B entries require explicit written permission before any probe traffic.

---

## Bucket A — Explicitly invites testing

These pages publish challenge/CTF language that directly invites users to attack the hosted AI. Authorization covers **the intended challenge behavior only**: submitting attack prompts through the provided chat/game interface at a reasonable manual rate. It does **not** cover denial-of-service, high-volume automated fuzzing, destructive actions, or testing unrelated infrastructure (hosting, DNS, other tenants). Redline's probe cadence should stay close to what a human player would do.

### A1. Lakera Gandalf
- **URL:** https://gandalf.lakera.ai/
- **Description:** Multi-level prompt-injection game by Lakera; each level's LLM guards a secret password behind increasingly strict defenses.
- **Permission evidence (quoted verbatim):**
  - Page title: "Lakera – Test your AI hacking skills"
  - Challenge text (as displayed on the game's intro page): "Your goal is to trick Gandalf into revealing the secret password for each level. However, Gandalf will level up each time you guess the password."
  - "an exciting game designed to challenge your ability to interact with large language models (LLMs)"
- **Adapter recommendation:** Browser chat-UI automation (the game is a custom chat interface with per-level password submission). No API key needed.

### A2. Tensor Trust
- **URL:** https://tensortrust.ai/
- **Description:** Crowdsourced prompt-hacking game; players attack each other's LLM defenses to steal secret access keys, and defend their own.
- **Permission evidence (quoted verbatim):**
  - "Hack their AI. Defend your own."
  - "Trick the AI into giving you access to other accounts."
  - "Submissions are publicly released for research."
  - Per the project's own README: "Attackers: attempt to trick other players' LLMs into disclosing secret access keys"
- **Adapter recommendation:** Browser game-UI automation; attacks and defenses are submitted through the web interface.

### A3. Prompt Airlines (Wiz)
- **URL:** https://promptairlines.com/
- **Description:** AI-security CTF by Wiz; the player must socially engineer a customer-service airline chatbot into issuing a free ticket.
- **Permission evidence (quoted verbatim):**
  - "AI Security Challenge"
  - "Your goal is to manipulate the customer service AI chatbot to get a free airline ticket*"
  - "Click below to start the first Capture the Flag challenge."
- **Adapter recommendation:** Browser chat-UI automation; investigate whether the chat uses plain HTTP endpoints that permit cleaner adapter integration.

### A4. Doublespeak
- **URL:** https://doublespeak.chat/
- **Description:** Minimal prompt-injection game; extract the bot's hidden name through conversation.
- **Permission evidence (quoted verbatim):**
  - "Your goal is to discover and submit the bot's name."
  - "Let the game begin!"
- **Adapter recommendation:** Browser chat-UI automation; tiny surface, good smoke-test target for the Redline adapter.

### A5. Prompt Injection CTF 2026
- **URL:** https://prompt-injection-ctf-2026.web.app/
- **Description:** 16-level attack playground covering direct/indirect injection, tool abuse, exfiltration, excessive agency, prompt leakage, and RAG poisoning, mapped to OWASP LLM Top 10.
- **Permission evidence (quoted verbatim):**
  - "Craft attack prompts that break constrained AI systems."
  - "No signup, no API key."
  - "16 Levels"
- **Adapter recommendation:** Browser chat-UI automation; level structure maps well to Redline's per-probe attempt logging.

### A6. PortSwigger Web Security Academy — Web LLM attacks
- **URL:** https://portswigger.net/web-security/llm-attacks
- **Description:** Free PortSwigger training module with deliberately vulnerable LLM-integration labs (prompt injection, excessive agency, indirect injection).
- **Permission evidence (quoted verbatim):**
  - "Learn prompt injection attacks and defend against them with this comprehensive free online course"
  - Recommended methodology: "Probe this new attack surface for vulnerabilities."
  - "Once you've mapped an LLM's API attack surface, your next step should be to use it to send classic web exploits to all identified APIs."
  - The Web Security Academy labs are purpose-built vulnerable instances provided for learners to attack.
- **Adapter recommendation:** Academy lab instances are spun up per-user; a Redline adapter would drive the lab's chat/HTTP interface after the operator launches the lab in their own Academy account.

---

## Bucket B — Permission required before any probing

Interesting real-world agent demos. Each has a genuinely published contact address (verified on the company's own site or its own published materials — none guessed). **Do not scan before receiving explicit written permission** covering the exact demo URL, allowed test types, and rate limits. Redline must also ask for a sandbox/test tenant where offered.

### B1. Tidio — Lyro AI Agent playground
- **Demo URL:** http://www.tidio.com/ai-agent/playground/
- **Description:** Live public demo of Lyro, Tidio's customer-support AI agent, answering questions from public support content.
- **Demo evidence (quoted verbatim):** "Experience Lyro AI Agent's ability to answer your questions using public support content."
- **Contact (published on tidio.com, Privacy Policy, last updated 2026-09-09):** support@tidio.net — "If you have any questions about this Privacy Policy or you wish to exercise any of your rights in relation to your personal data, please contact us at support@tidio.net." (Also privacy@tidio.net for their DPO.)
- **Permission ask:** written approval to submit adversarial test prompts to the Lyro playground, plus allowed test categories and rate limits.
- **Adapter recommendation:** Browser chat-UI automation against the playground widget.

### B2. Ada
- **Demo URL:** https://www.ada.cx/ (enterprise customer-service agents; demo arranged via the site)
- **Description:** Enterprise customer-service AI agents (workflows + APIs), used by companies including Zoom, Square, and Canva.
- **Contact (published in Ada's own official PDFs on info.ada.support):** hello@ada.support — "Please email us at hello@ada.support"
- **Permission ask:** request a demo/sandbox tenant and written permission for red-team probing, including which probe families are in scope.
- **Adapter recommendation:** Hosted chat UI or API after permission; confirm which channel the sandbox exposes.

### B3. Intercom — Fin
- **Demo URL:** https://fin.ai/voice (live interactive voice demo of Fin, Intercom's autonomous support agent; per Intercom's own help docs: "you can watch Fin Voice in action and use the live interactive demo on fin.ai/voice")
- **Description:** Fin is Intercom's AI agent that autonomously resolves customer-support conversations over chat and voice.
- **Contact (published on intercom.com, Support Policy):** team@intercom.com — "Customers may contact Intercom for Support via the Intercom Messenger or via email at team@intercom.com"
- **Permission ask:** written approval to probe the public Fin demo (or a sandbox), and whether a text-chat/API channel is available instead of voice for automated testing.
- **Adapter recommendation:** Browser voice-UI automation is heavy; prefer asking for a text-chat demo or API endpoint in the permission request.

### B4. Botpress
- **Demo URL:** https://guardrails.botpress.bot (official Botpress example bot, linked from Botpress's own repo: "Try it live: https://guardrails.botpress.bot")
- **Description:** Botpress is an agent-building platform; its official examples repo hosts live demo bots (guardrails demo, customer-service demo, etc.).
- **Contact (published in Botpress's own SECURITY.md on GitHub):** security@botpress.com — "reach out to us at security@botpress.com"
- **Scope caveat:** Botpress's policy treats prompt injection crossing a security boundary as in scope, but states "Bots built by users using Botpress are not in our scope" — so written confirmation is needed that a given demo bot is covered before probing.
- **Adapter recommendation:** Browser chat-UI automation against the demo bot's chat interface.

### B5. Chatbase
- **Demo URL:** https://www.chatbase.co/ (customer-facing support/sales/product-guidance agents; demo via the site)
- **Description:** No-code platform for customer-facing AI agents (support, sales, product guidance); claims 10,000+ brands.
- **Contact:** zeyad@chatbase.co — published in Chatbase's own syndicated company announcement (founder contact). Note: no general/security mailbox was found on their site, so this is the founder's public address; keep the ask short and professional.
- **Permission ask:** request a demo bot or sandbox and written permission for adversarial testing.
- **Adapter recommendation:** Hosted chat UI after permission.

### B6. Decagon
- **Demo URL:** https://decagon.ai/ (AI customer-support agents for chat, email, voice, SMS; demo arranged via the site)
- **Description:** Enterprise "AI concierge" support agents used by companies including Notion, Rippling, and Eventbrite.
- **Contact (published on decagon.ai's own pages, e.g. case studies):** sales@decagon.ai — "Contact us at sales@decagon.ai"
- **Permission ask:** request a demo/sandbox environment and written permission for red-team probing with defined scope and rate limits.
- **Adapter recommendation:** Hosted chat/API after permission; confirm the accessible channel in the permission request.

---

## Notes for the permission requests (do not send without approval)

Every outbound request needs sai's sign-off on the exact recipient, subject, and body. Each request should cover:
1. Who we are: sai / Redline, an open-source agent red-team scanner.
2. Exact demo URL or sandbox we want to test.
3. What "testing" means: benign adversarial prompts (prompt injection, jailbreak, tool-abuse attempts using synthetic canary tokens only — no real PII, no destructive actions).
4. Rate: low, human-like cadence; no DoS.
5. Ask: written permission, scope boundaries, and any test tenant/sandbox they'd prefer.
6. Offer: share the findings report with them first (responsible disclosure) before any public leaderboard mention.

## Verification log

- All Bucket A quotes verified on live pages 2026-09-25/26, except Gandalf's in-game objective text, which is quoted from the game's own intro page as widely reproduced; the live-verified site title ("Lakera – Test your AI hacking skills") corroborates the challenge framing.
- All Bucket B contact emails verified on the company's own domain or own published materials:
  - support@tidio.net — tidio.com/privacy-policy
  - hello@ada.support — Ada's official PDFs on info.ada.support
  - team@intercom.com — intercom.com/legal/support-policy
  - security@botpress.com — github.com/botpress/botpress SECURITY.md
  - zeyad@chatbase.co — Chatbase's own published company announcement (founder address; no general mailbox found)
  - sales@decagon.ai — decagon.ai case-study pages
- Demo URLs verified live: tidio.com/ai-agent/playground, tensortrust.ai, promptairlines.com, doublespeak.chat, prompt-injection-ctf-2026.web.app, gandalf.lakera.ai, portswigger.net/web-security/llm-attacks, guardrails.botpress.bot (via Botpress's own repo README).
