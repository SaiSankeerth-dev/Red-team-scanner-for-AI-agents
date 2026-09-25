# Redline dashboard

Next.js dashboard for the Redline agent red-team scanner: browse past
campaigns, see scored breakdowns and findings, and launch new scans.

## Run it

```bash
# 1. Start the Redline API (from the repo root)
redline serve            # http://localhost:8000

# 2. In another terminal, start the dashboard
cd dashboard
cp .env.example .env     # point NEXT_PUBLIC_REDLINE_API at your API if needed
npm install
npm run dev              # http://localhost:3000
```

## What it shows

- **Campaigns** — every scan with its A–F grade badge, score, and fail/blocked counts
- **Campaign detail** — scorecard, per-probe breakdown table, and all findings with
  full transcripts and remediation advice
- **New scan** — run a scan against a local demo, an OpenAI-compatible endpoint,
  or any generic HTTP agent endpoint
- Links out to the full standalone **HTML report** and the **PDF export**
