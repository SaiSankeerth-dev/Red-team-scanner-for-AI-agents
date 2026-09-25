"""Redline CLI."""
from __future__ import annotations

import argparse
import sys
from collections import Counter

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # .env support is optional; env vars still work

from redline.adapters.local import LocalAgentAdapter
from redline.demo import DEMO_TARGETS
from redline.probes.canary_leak import CanaryLeakProbe
from redline.probes.direct_injection import DirectInjectionProbe
from redline.probes.jailbreak import JailbreakProbe
from redline.probes.excessive_agency import ExcessiveAgencyProbe
from redline.probes.indirect_injection import IndirectInjectionProbe
from redline.probes.prompt_extraction import PromptExtractionProbe
from redline.probes.refusal_consistency import RefusalConsistencyProbe
from redline.probes.tool_exfiltration import ToolExfiltrationProbe

PACKS = {
    "basics": [
        DirectInjectionProbe,
        PromptExtractionProbe,
        CanaryLeakProbe,
        JailbreakProbe,
        RefusalConsistencyProbe,
        IndirectInjectionProbe,
        ToolExfiltrationProbe,
        ExcessiveAgencyProbe,
    ],
}

LEGEND = "[pass] = attack blocked   [partial] = unclear   [fail] = attack SUCCEEDED (target is vulnerable)"


def _print_results(result) -> None:
    for probe, attempts in result.by_probe:
        print(f"## {probe.name}  (severity: {probe.severity})")
        print(f"   {probe.description}")
        for out in attempts:
            resp = (out.response or "").replace("\n", " ")
            line = f"   [{out.verdict}] {resp[:90]}"
            if out.notes:
                line += f"  ({out.notes})"
            print(line)
        if hasattr(probe, "summarize"):
            verdict, note = probe.summarize(attempts)
            print(f"   [{verdict}] summary: {note}")
        print()


def cmd_scan(args: argparse.Namespace) -> int:
    from redline.adapters.factory import build_adapter

    headers = {}
    for h in args.http_header or []:
        if "=" not in h:
            print(f"[redline] bad --http-header (want KEY=VALUE): {h}")
            return 2
        k, v = h.split("=", 1)
        headers[k.strip()] = v.strip()
    try:
        target, target_name = build_adapter(
            args.adapter,
            {
                "target": args.target,
                "base_url": args.base_url,
                "api_key": args.api_key,
                "model": args.model,
                "system_prompt": args.system_prompt,
                "url": args.http_url,
                "response_path": args.http_response_path,
                "headers": headers,
            },
        )
    except ValueError as e:
        print(f"[redline] {e}")
        return 2
    probe_classes = PACKS.get(args.pack)
    if probe_classes is None:
        print(f"[redline] unknown pack: {args.pack} (try: {', '.join(PACKS)})")
        return 2

    from redline.runner import CampaignRunner
    from redline.store.db import session_scope

    judge = None
    if args.judge:
        from redline.judge.llm import LLMJudge

        try:
            judge = LLMJudge.from_env()
            print("[redline] LLM judge enabled for ambiguous cases")
        except RuntimeError as e:
            print(f"[redline] warning: {e} — continuing deterministic-only")

    with session_scope(args.db) as session:
        runner = CampaignRunner(session, judge=judge)
        result = runner.run_campaign(
            name=args.name or f"{target_name}/{args.pack}",
            target=target,
            target_name=target_name,
            probe_classes=probe_classes,
            pack_name=args.pack,
        )

    print(f"[redline] target={target_name} pack={args.pack}")
    print(f"[redline] {LEGEND}\n")
    _print_results(result)
    counts = result.verdict_counts()
    summary = " ".join(f"{v}={counts.get(v, 0)}" for v in ("fail", "partial", "pass"))
    print(f"[redline] saved campaign #{result.campaign.id}  ({summary})")
    return 0


def cmd_campaigns(args: argparse.Namespace) -> int:
    from redline.store.db import session_scope
    from redline.store.models import Campaign

    with session_scope(args.db) as session:
        campaigns = (
            session.query(Campaign).order_by(Campaign.id.desc()).limit(args.limit).all()
        )
        if not campaigns:
            print("[redline] no campaigns yet — run `redline scan` first")
            return 0
        for c in campaigns:
            counts: Counter = Counter(a.verdict for a in c.attempts)
            summary = " ".join(f"{v}={counts.get(v, 0)}" for v in ("fail", "partial", "pass"))
            print(
                f"#{c.id}  {c.name}  target={c.target} pack={c.pack}  "
                f"{c.created_at:%Y-%m-%d %H:%M}  {summary}"
            )
    return 0


def cmd_calibrate(args: argparse.Namespace) -> int:
    from redline.judge.calibration import calibrate, load_cases
    from redline.judge.llm import LLMJudge

    try:
        judge = LLMJudge.from_env()
    except RuntimeError as e:
        print(f"[redline] {e}")
        print("[redline] copy .env.example to .env and add your key to run calibration.")
        return 2

    cases = load_cases()
    if args.n:
        cases = cases[: args.n]
    report = calibrate(judge, cases)
    print(
        f"[redline] judge accuracy: {report['correct']}/{report['total']} "
        f"({report['accuracy']:.0%})"
    )
    for m in report["mismatches"]:
        print(f"  MISMATCH [{m['probe']}] expected={m['expected']} got={m['got']}: {m['note']}")
        print(f"    response: {m['response'][:100]}")
    return 0 if report["accuracy"] >= 0.9 else 1


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    print(f"[redline] serving API on http://{args.host}:{args.port}")
    uvicorn.run("redline.api.app:app", host=args.host, port=args.port)
    return 0


def cmd_spend(args: argparse.Namespace) -> int:
    from redline.judge.spend import month_spent_usd, monthly_budget_usd, spend_file

    spent = month_spent_usd()
    cap = monthly_budget_usd()
    pct = min(100, spent / cap * 100) if cap else 0
    bar = "#" * int(pct / 5) + "-" * (20 - int(pct / 5))
    print(f"[redline] judge spend this month: ${spent:.4f} / ${cap:.2f}")
    print(f"[redline] [{bar}] {pct:.0f}%")
    print(f"[redline] log: {spend_file()}")
    print("[redline] set REDLINE_MONTHLY_BUDGET_USD to change the cap")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    from redline.reports.generator import build_report_data, write_html_report
    from redline.store.db import session_scope

    with session_scope(args.db) as session:
        try:
            data = build_report_data(session, args.campaign_id)
        except LookupError as e:
            print(f"[redline] {e}")
            return 2

    out_base = args.out or f"./reports/redline-campaign-{args.campaign_id}"
    paths = []
    if args.format in ("html", "both"):
        paths.append(write_html_report(data, out_base + ".html"))
    if args.format in ("pdf", "both"):
        from redline.reports.pdf import write_pdf_report

        paths.append(write_pdf_report(data, out_base + ".pdf"))
    print(f"[redline] campaign #{args.campaign_id}: score {data['score']}/100 "
          f"(grade {data['grade']}), {data['counts']['fail']} findings")
    for p in paths:
        print(f"[redline] wrote {p}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="redline",
        description="Automated red-team scanner for AI agents",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("scan", help="Run a probe campaign against a target")
    s.add_argument("--target", default="vulnerable",
                   help=f"Target to attack (try: {', '.join(DEMO_TARGETS)})")
    s.add_argument("--pack", default="basics",
                   help=f"Probe pack to run (try: {', '.join(PACKS)})")
    s.add_argument("--name", default=None, help="Campaign name")
    s.add_argument("--db", default=None, help="DB URL (default: DATABASE_URL or ./redline.db)")
    s.add_argument("--judge", action="store_true",
                   help="Use the LLM judge for ambiguous cases (needs OPENAI_API_KEY)")
    s.add_argument("--adapter", default="local", choices=["local", "openai", "http"],
                   help="How to reach the target (default: local demo agents)")
    s.add_argument("--base-url", default=None,
                   help="OpenAI-compatible base URL (default: OPENAI_BASE_URL or https://api.openai.com/v1)")
    s.add_argument("--api-key", default=None,
                   help="API key (default: TARGET_API_KEY or OPENAI_API_KEY env)")
    s.add_argument("--model", default="gpt-4o-mini", help="Model name for the openai adapter")
    s.add_argument("--system-prompt", default=None,
                   help="System prompt to prepend for the openai adapter")
    s.add_argument("--http-url", default=None, help="Endpoint URL for the http adapter")
    s.add_argument("--http-response-path", default="response",
                   help="Dotted JSON path to the reply (default: response)")
    s.add_argument("--http-header", action="append", default=[],
                   help="Extra header for the http adapter (KEY=VALUE, repeatable)")
    s.set_defaults(func=cmd_scan)

    c = sub.add_parser("campaigns", help="List past campaigns")
    c.add_argument("--limit", type=int, default=10)
    c.add_argument("--db", default=None, help="DB URL (default: DATABASE_URL or ./redline.db)")
    c.set_defaults(func=cmd_campaigns)

    k = sub.add_parser("calibrate", help="Score the LLM judge against labeled cases")
    k.add_argument("--n", type=int, default=0, help="Only score the first N cases")
    k.set_defaults(func=cmd_calibrate)

    r = sub.add_parser("report", help="Generate a scored HTML/PDF report for a campaign")
    r.add_argument("campaign_id", type=int)
    r.add_argument("--format", choices=["html", "pdf", "both"], default="html")
    r.add_argument("--out", default=None,
                   help="Output path without extension (default: ./reports/redline-campaign-<id>)")
    r.add_argument("--db", default=None, help="DB URL (default: DATABASE_URL or ./redline.db)")
    r.set_defaults(func=cmd_report)

    v = sub.add_parser("serve", help="Start the Redline API server (dashboard backend)")
    v.add_argument("--host", default="127.0.0.1")
    v.add_argument("--port", type=int, default=8000)
    v.set_defaults(func=cmd_serve)

    sp = sub.add_parser("spend", help="Show this month's LLM judge spend vs budget")
    sp.set_defaults(func=cmd_spend)

    from redline.canary_receiver import cmd_canary_new, cmd_canary_watch

    cn = sub.add_parser("canary", help="Mint a fresh canary token + hit URL")
    cn.add_argument("--label", default="", help="Label for this canary")
    cn.set_defaults(func=cmd_canary_new)

    cw = sub.add_parser(
        "canary-watch", help="Run the canary hit receiver (tripwire listener)"
    )
    cw.add_argument("--port", type=int, default=8787)
    cw.set_defaults(func=cmd_canary_watch)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
