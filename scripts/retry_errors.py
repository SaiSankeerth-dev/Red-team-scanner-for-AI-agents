"""Retry a campaign's 'target error' attempts with a fresh adapter session.

Usage:
    .venv/bin/python scripts/retry_errors.py <campaign_id> <adapter_kind> [--delay SECS] [--db PATH]

Only touches attempts whose notes contain 'target error'. Re-sends the exact
same messages, re-runs the probe's deterministic detector, and updates the
record. Use a gentler delay than the original campaign if the target was
rate-limiting.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    campaign_id = int(sys.argv[1])
    kind = sys.argv[2]
    delay = 8.0
    db = None
    args = sys.argv[3:]
    if "--delay" in args:
        delay = float(args[args.index("--delay") + 1])
    if "--db" in args:
        db = args[args.index("--db") + 1]

    from redline.adapters.ctf import (
        GandalfAdapter,
        PromptAirlinesAdapter,
        RateLimitedAdapter,
    )
    from redline.cli import PACKS
    from redline.probes.base import Attempt
    from redline.store.db import session_scope
    from redline.store.models import AttemptRecord

    probe_by_name = {}
    for pack in PACKS.values():
        for cls in pack:
            probe_by_name[cls.name] = cls

    if kind == "gandalf":
        inner = GandalfAdapter()
    elif kind == "promptairlines":
        inner = PromptAirlinesAdapter()
    else:
        print(f"[retry] unknown adapter kind: {kind}")
        return 2
    adapter = RateLimitedAdapter(inner, delay=delay)
    print(f"[retry] adapter={kind} delay={delay}s")

    with session_scope(db) as session:
        recs = (
            session.query(AttemptRecord)
            .filter(
                AttemptRecord.campaign_id == campaign_id,
                AttemptRecord.notes.like("%target error%"),
            )
            .all()
        )
        print(f"[retry] campaign #{campaign_id}: {len(recs)} error attempts")
        fixed = 0
        for rec in recs:
            cls = probe_by_name.get(rec.probe_name)
            if cls is None:
                print(f"[retry] unknown probe {rec.probe_name}, skipping")
                continue
            probe = cls()
            attempt = Attempt(
                probe_name=rec.probe_name, messages=list(rec.messages)
            )
            try:
                out = probe.run(adapter, attempt)
            except Exception as e:  # noqa: BLE001
                rec.notes = (rec.notes or "") + f" [retry failed: {e}]"
                print(f"[retry] {rec.probe_name}: still failing ({e})")
                continue
            rec.response = out.response
            rec.verdict = out.verdict or "partial"
            rec.notes = (
                (rec.notes or "")
                + f" [retried ok, verdict={rec.verdict}]"
            )
            fixed += 1
            print(f"[retry] {rec.probe_name}: error -> {rec.verdict}")
        session.commit()
    print(f"[retry] done: {fixed}/{len(recs)} recovered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
