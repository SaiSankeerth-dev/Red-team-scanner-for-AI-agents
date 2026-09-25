# Contributing

Redline is a small, focused codebase. A few conventions keep it that way:

## Probes

- Every probe lives in `redline/probes/<name>.py` and subclasses `Probe`.
- Detectors are **deterministic first**: string matching, regex, tool-call
  inspection. The LLM judge is a tiebreaker for `partial` verdicts only —
  never the source of truth.
- Each probe ships with attempts in `generate_attempts()` and a pure
  `detect_success(attempt)` with no network calls, so tests stay fast and
  hermetic.
- Register new probes in `PACKS` in `redline/cli.py`.

## Demo targets

- New archetypes go in `redline/demo/` and must be registered in
  `DEMO_TARGETS` (`redline/demo/__init__.py`).
- The dogfood CI asserts exact scorecards: `vulnerable` → 0/F,
  `hardened` → 100/A. If your change moves those, the change is wrong —
  fix the demo, not the assertion.

## Tests

- `pytest -q` must stay green. Add tests alongside features, not after.
- No live network in tests. No real secrets anywhere — use synthetic
  canaries (`sk-fake-…`, `acme-admin-123`).

## Reports

- If you add a probe, add its remediation text to `REMEDIATION` in
  `redline/reports/generator.py` — every finding ships with a fix.
