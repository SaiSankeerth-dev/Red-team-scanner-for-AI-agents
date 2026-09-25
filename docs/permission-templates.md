# Permission outreach templates

Redline only scans systems the owner has permitted. These templates are the
ask-first workflow: permission request → scan → heads-up before publishing.
They double as a cold-email opener — every "yes" is a conversation with a
builder who now knows your name.

Rule: no scan without a written yes. A demo being public is not permission.

---

## 1. Permission request (cold)

**Subject:** quick security test of {{demo_name}} — 2 min of your time, free report

Hi {{name}},

I'm Sai, a CS student building Redline — an open-source scanner that
red-teams AI agents for prompt injection, jailbreaks, and tool-based data
exfiltration (think npm audit, but for agents).

I came across {{demo_name}} and would love to include it in a public
leaderboard of agent security postures I'm publishing. Before I run anything,
I wanted your explicit permission.

What the scan does:
- ~27 automated attacks (prompt injection, jailbreaks, extraction attempts)
- Uses only fake canary tokens — nothing real is ever at risk or published
- Read-only from your side: no data modified, no accounts touched
- You get the full scored report + remediation notes before anything goes public

If you're open to it, just reply "yes" and tell me the best endpoint/URL to
test. If you'd rather not, no worries at all — I won't touch it.

Thanks,
Sai Sankeerth Voorugonda
https://github.com/SaiSankeerth-dev/Red-team-scanner-for-AI-agents

---

## 2. Follow-up (3 days, no reply)

**Subject:** re: quick security test of {{demo_name}}

Hi {{name}},

Bumping this once in case it got buried — I'd love to include {{demo_name}}
in a public agent-security leaderboard, but only with your permission.

One-line version: I run ~27 automated red-team attacks using fake secrets,
send you the full report first, and publish only with your okay.

Worth a "yes"? If not, I'll leave it alone.

— Sai

---

## 3. Heads-up before publishing findings (after a "yes" + scan)

**Subject:** your Redline report for {{demo_name}} — publishing {{date}}

Hi {{name}},

The scan of {{demo_name}} is done. Attached is your full report: score,
grade, and every finding with reproduction transcripts and fix suggestions.

I'm publishing the leaderboard on {{date}}. Your entry will show:
- Target name, score, grade, and fail/blocked counts
- Bug *classes* found (e.g. "indirect injection via retrieved docs") —
  never payloads, never anything resembling real data

If you want anything reworded, or you'd like to fix first and be re-scanned
before publication, just say the word — happy to hold the post.

Thanks for letting me test it.

— Sai

---

## 4. If they say no

Thank them, log it, never scan. A gracious "no problem, thanks for replying"
keeps the door open — several builders say yes on the second project.
