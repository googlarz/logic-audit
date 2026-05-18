# logic-audit — Live Demo

This is a real audit run on three real files in [`demo/`](demo/). The bugs were planted — but the audit output is genuine: every finding was produced by running the skill's phases against the actual files, with tool calls made during this session.

**Artifact set:**
- [`demo/api-spec.md`](demo/api-spec.md) — API specification for a payments endpoint
- [`demo/payments.py`](demo/payments.py) — Python implementation
- [`demo/test_payments.py`](demo/test_payments.py) — pytest test suite

---

## Audit output

```
Mode: full. Authority: api-spec.md > payments.py > test_payments.py.
Artifacts: 3. Check order: 2.5, 2.1, 2.7, 2.6, 2.3, 2.2.
Findings: 2 CRITICAL · 4 HIGH · 1 MINOR.
Assumptions: 4 extracted · 2 tested (50%) · A1, A4 skipped: 0 chains depend on them.
Self-audit: 0 dropped · 0 reclassified.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Fix these first

1. C1 — every success/error key in the response schema is wrong; all 4 tests fail at assertion level
2. C2 — spec says `amount` is in cents; implementation treats it as dollars; callers following the spec get charged 100×
3. H2 — idempotency_key is accepted but silently ignored; duplicate charges will occur

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## CRITICAL

[C1] contradiction  payments.py:44–46 vs api-spec.md:20–22 vs test_payments.py:8–9
  "success": True, "id": data["id"]"           [v: grep '"success"' payments.py → lines 25,44,49,51,53,58]
  '"status": "ok", "transaction_id": "txn_abc123"'  [v: read api-spec.md:20–21 → confirmed]
  Why: success key is "success" (bool) in implementation, "status" (string) in spec and tests.
  ID key is "id" in implementation, "transaction_id" in spec and tests. Every caller checking
  result["status"] == "ok" or "transaction_id" in result gets a KeyError or False — silently.
  Tests were written against the spec, not the implementation. All 4 tests fail at assertion level.
  Evidence: Direct. Confidence: High. Depends-on: —.
  Fix: rename keys in payments.py: "success": True → "status": "ok", "id" → "transaction_id".
  Same for error paths: "success": False, "error" → "status": "error", "code".

[C2] contradiction  payments.py:20 vs api-spec.md:12
  "Amount in dollars (e.g. 10.00 for $10.00)"   [v: grep 'amount.*dollars' payments.py → line 20]
  "Amount in **cents** (e.g. 1000 = $10.00)"    [v: grep 'cents' api-spec.md → line 12]
  Why: the interface contract is undefined. The docstring says dollars; the spec says cents.
  The internal conversion (amount * 100) is correct if callers pass dollars — but any client
  that follows the spec and passes cents (e.g. 1000 for $10) triggers a $1,000 charge.
  test_payments.py passes 10.00 (dollars) — consistent with the docstring, contradicting the spec.
  Evidence: Direct. Confidence: High. Depends-on: —.
  Fix: pick one. Recommended: follow the spec — accept cents (integer), remove the * 100
  conversion, update the docstring, update tests to pass 1000 instead of 10.00.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## HIGH

[H1] contradiction  payments.py:4 vs api-spec.md:41
  "MAX_RETRIES = 5"                        [v: grep 'MAX_RETRIES' payments.py → line 4]
  "Maximum **3 retries** on network timeout"  [v: grep '3 retries' api-spec.md → line 41]
  Why: implementation retries 5 times on timeout; spec guarantees at most 3. Callers
  timing their own timeout budgets against the spec's promise will see unexpected latency.
  Evidence: Direct. Confidence: High. Depends-on: —.
  Fix: change MAX_RETRIES = 5 to MAX_RETRIES = 3.

[H2] absence  payments.py:13 vs api-spec.md:14
  Claim:  "idempotency_key: str = None"  [v: grep 'idempotency' payments.py → line 13]
  Absent: any use of idempotency_key in the function body — it is accepted but never read
  Evidence: grep 'idempotency_key' payments.py returns only lines 13 (signature) and 22
  (docstring). Zero use in payload or request headers.  [v: grep 'idempotency_key' payments.py → lines 13, 22 only]
  Impact: spec guarantees "duplicate requests with the same idempotency_key within 24 hours
  return the original response without re-charging." That guarantee is silently broken.
  A caller passing idempotency_key on a retry will be double-charged.
  Evidence: Inferred — param declared and documented; body never references it. Confidence: High.
  Depends-on: —.

[H3] absence  payments.py (no handler) vs api-spec.md:38
  Claim:  "Returns ERR_INSUFFICIENT_FUNDS if balance check fails before charge"
          [v: grep 'ERR_INSUFFICIENT_FUNDS' api-spec.md → line 38]
  Absent: any path in payments.py that returns ERR_INSUFFICIENT_FUNDS
          [v: grep 'ERR_INSUFFICIENT_FUNDS' payments.py → 0 matches]
  Impact: insufficient funds responses from the payment processor fall through to the
  generic ERR_UNKNOWN path. Callers cannot distinguish "card declined" from "insufficient
  funds" — different UX actions are required for each.
  Evidence: Inferred — spec lists the code; implementation grep returns nothing. Confidence: High.
  Depends-on: —.

[H4] absence  payments.py:53,58 vs api-spec.md:31
  Claim:  '"code": "ERR_INSUFFICIENT_FUNDS | ERR_CARD_DECLINED | ERR_INVALID_CUSTOMER"'
          [v: grep 'ERR_' api-spec.md → line 31 — 3 codes listed]
  Absent: ERR_UNKNOWN and ERR_TIMEOUT are not in the spec's error code list
          [v: grep 'ERR_UNKNOWN\|ERR_TIMEOUT' api-spec.md → 0 matches]
  Impact: callers that enumerate the spec's error codes will not handle ERR_UNKNOWN or
  ERR_TIMEOUT — unhandled error strings reach the application layer silently.
  Evidence: Inferred — 2 codes present in implementation, absent from spec. Confidence: High.
  Depends-on: —.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MINOR

[M1] test_payments.py:24–27  test_amount_in_cents makes the wrong assertion
  Claim: "# Verify the function handles cent-denominated amounts"  [v: read test_payments.py:25 → confirmed]
  The test passes charge_customer("cus_123", 100) and asserts amount_charged == 100.
  Under the current implementation (dollars interpretation), 100 * 100 = 10_000, so the
  assertion fails. Under a corrected cents implementation, amount_charged would be 100 —
  but that would mean charging $1.00, not $100. The test name and assertion are in tension:
  it appears to test the unit convention but doesn't verify which unit is actually used.
  Innocent explanation: the author may have intended this as a placeholder test.
  Evidence: Circumstantial. Confidence: Low. Depends-on: C2.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## OK

✓ 2.1 Reference resolution — no cross-file symbol imports; conceptual references (error
  codes, retry count) all checked directly.
  How checked: grepped each ERR_ code in both files; grepped retry count in both files.
✓ 2.4 Causal & temporal — no dated events or ordering dependencies in this artifact set.
  How checked: scanned all three files for dates, timestamps, ordering language — none found.
✗ 2.8 Boundary & edge — skipped: no numeric boundary conditions beyond retry count (covered by H1).
✗ 2.10 Realism — skipped: no placeholder markers found in quick scan; no statistical data.
✗ 2.11 Version history — skipped: demo files not in git history.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## Assumptions register

[A1] test_payments.py "charge_customer accepts amount in dollars"  Relational
  Impact: 0 chains.  Likelihood: High (contradicted by spec).  Triage: L×H
  Tested: no — depends on C2 resolution; skip until C2 is fixed.

[A2] test_payments.py "response has 'status' and 'transaction_id' keys"  Relational
  Impact: 2 chains.  Likelihood: High (C1 shows it's already false).  Triage: H×H
  Tested: yes → C1 (assumption false — implementation uses different keys)

[A3] api-spec.md "all error codes callers encounter are listed in the error response schema"  Structural
  Impact: 1 chain.  Likelihood: High.  Triage: H×H
  Tested: yes → H3, H4 (ERR_INSUFFICIENT_FUNDS missing from impl; ERR_UNKNOWN + ERR_TIMEOUT missing from spec)

[A4] payments.py "callers never pass idempotency_key expecting deduplication"  Relational
  Impact: 0 chains independently.  Likelihood: Medium.  Triage: L×M
  Tested: no — H2 already covers the structural gap; this assumption adds no new chains.
```

---

## What the audit found

| ID | Severity | Root cause |
|----|----------|------------|
| C1 | CRITICAL | Response schema evolved independently in spec vs implementation — two different key names for every field |
| C2 | CRITICAL | `amount` unit undefined at the interface — docstring says dollars, spec says cents, no enforcement |
| H1 | HIGH | Magic number `MAX_RETRIES = 5` contradicts spec guarantee of max 3 |
| H2 | HIGH | `idempotency_key` parameter is declared and documented but never used in the function body |
| H3 | HIGH | `ERR_INSUFFICIENT_FUNDS` specified but never returned — unreachable code path |
| H4 | HIGH | `ERR_UNKNOWN` and `ERR_TIMEOUT` returned but not in spec — undocumented error surface |
| M1 | MINOR | `test_amount_in_cents` asserts the wrong value regardless of which unit convention wins |

**All 4 tests in `test_payments.py` currently fail at assertion level** — they were written against the spec's response shape, not the implementation's. This is the classic symptom of C1: spec and implementation diverged silently, tests lagged behind.

---

## Install and try it yourself

```bash
mkdir -p ~/.claude/skills/logic-audit
cp SKILL.md ~/.claude/skills/logic-audit/SKILL.md
```

Then in Claude Code:
```
/logic-audit demo/api-spec.md demo/payments.py demo/test_payments.py
```
