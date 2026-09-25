"""Re-run the LLM judge over a campaign's 'partial' attempts.

Usage:
    JUDGE_API_KEY=... JUDGE_BASE_URL=... JUDGE_MODEL=... \
        .venv/bin/python scripts/rejudge.py <campaign_id> [--db PATH]

Only touches attempts currently marked 'partial'; leaves everything else
alone. Deterministic verdicts are never overridden.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def main() -> int:
    campaign_id = int(sys.argv[1])
    db = None
    if "--db" in sys.argv:
        db = sys.argv[sys.argv.index("--db") + 1]

    from redline.judge.llm import LLMJudge
    from redline.judge.spend import BudgetExceeded
    from redline.store.db import session_scope
    from redline.store.models import AttemptRecord

    judge = LLMJudge.from_env()
    print(f"[rejudge] judge model: {judge.model}")

    with session_scope(db) as session:
        partials = (
            session.query(AttemptRecord)
            .filter(
                AttemptRecord.campaign_id == campaign_id,
                AttemptRecord.verdict == "partial",
                # skip attempts with no real response (target errors),
                # unless they were later retried successfully
                ~(
                    AttemptRecord.notes.like("%target error%")
                    & ~AttemptRecord.notes.like("%retried ok%")
                ),
            )
            .all()
        )
        print(f"[rejudge] campaign #{campaign_id}: {len(partials)} partial attempts")
        judged = 0
        for rec in partials:
            try:
                verdict, rationale = judge.score(
                    rec.probe_name, rec.messages, rec.response or ""
                )
            except BudgetExceeded as e:
                print(f"[rejudge] budget exceeded, stopping: {e}")
                break
            except Exception as e:  # keep the partial, note the error
                rec.notes = (rec.notes + " " if rec.notes else "") + f"[rejudge error: {e}]"
                continue
            rec.verdict = verdict
            rec.notes = (rec.notes + " " if rec.notes else "") + f"[judge] {rationale}"
            judged += 1
            print(f"[rejudge] {rec.probe_name}: partial -> {verdict}")
        session.commit()
    print(f"[rejudge] done: {judged}/{len(partials)} resolved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
