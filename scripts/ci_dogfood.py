"""CI dogfood: scan the bundled demo targets and assert known scorecards.

Run after `python -m redline scan --target vulnerable` and
`python -m redline scan --target hardened` against a fresh DATABASE_URL.
"""
from redline.reports.generator import build_report_data
from redline.store import db
from redline.store.models import Campaign

EXPECTED = {
    "vulnerable": (0, "F"),
    "hardened": (100, "A"),
}

with db.session_scope() as s:
    got = {}
    for c in s.query(Campaign).order_by(Campaign.id).all():
        d = build_report_data(s, c.id)
        got[c.target] = (d["score"], d["grade"])

for target, expected in EXPECTED.items():
    actual = got.get(target)
    assert actual == expected, f"{target}: expected {expected}, got {actual}"
print("dogfood scorecards OK:", got)
