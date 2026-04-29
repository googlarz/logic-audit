# logic-audit

Cross-artifact logic and consistency auditor for Claude Code. Give it any set of related files — code + tests + docs, spec + implementation, prompt + output, data + analysis + chart — and it finds where they don't hang together.

Not a linter. Not a code reviewer. It finds the bugs that only exist *between* artifacts.

---

## The problem it solves

Most tools check one file at a time. But the nastiest bugs live in the gaps:

- The spec says `return None` on failure. The code `raise`s. The tests were written against the spec.
- The API contract says `amount` is in EUR. The dashboard code assumes USD.
- The config says `max_retries=3`. The implementation reads `max_retry` (typo). Silent default kicks in.
- The ADR says "we chose approach B because A has race condition X". The implementation uses approach A.

Logic-audit finds these by treating your artifact set as a system and checking it as a whole.

---

## How it works

Six phases, each feeding the next:

| Phase | What it does |
|-------|-------------|
| **0 — Scope** | Map artifact relationships. Declare authority order (spec > code > tests). Identify known gaps. Choose mode: full or proactive. |
| **1 — Inventory** | List every artifact. Extract hidden assumptions: structural, temporal, relational, domain. These become the Phase 4 test budget. |
| **2 — Checks** | 10 cross-artifact checks in priority order for your artifact type. Reference resolution, identity drift, quantifier consistency, causal ordering, I/O coherence, completeness, contradiction, boundary drift, self-reference, realism. |
| **3 — Inference chains** | Trace multi-hop dependency chains backward from Phase 2 findings. Find snap points — where a chain assumes something its inputs never establish. |
| **4 — Counterfactual stress test** | For each Phase 1 assumption and Phase 3 snap point: *if this were false, what else breaks?* Triaged by impact × likelihood. |
| **5 — Self-audit + report** | Re-read every cited location before publishing. Drop findings whose quotes don't match. Structured report with "Fix these first" summary. |

Phase 2 seeds Phase 3. Phase 3 seeds Phase 4. This is how multi-hop bugs get caught — the ones invisible when you check artifacts pairwise.

---

## What makes it different

**Structural verification gate.** Every Direct-evidence finding must carry a `[v: tool → result]` inline tag proving the quoted value was read from a tool call, not recalled from memory. Without it, the finding cannot be Direct. You cannot file a high-confidence finding without showing the receipt.

```
[C1] contradiction  auth.py:34 vs spec.md:14
  "raise ValueError("invalid token")"  [v: grep "raise" auth.py → line 34]
  "returns None on invalid token"      [v: read spec.md:14 → confirmed]
  Why: test suite written against spec; code raises — all error-path tests silently wrong.
  Evidence: Direct. Confidence: High. Fix: change auth.py to return None.
```

**Two finding schemas.** Contradiction findings cite both sides. Absence findings (snap points, missing handlers, unestablished preconditions) use `claim + absent + impact` — no fabricated opposing quote required.

**Evidence grading with hard ceilings.** Direct → High ceiling. Inferred → Medium. Circumstantial → Low. No exceptions. A finding that depends on a Medium finding is at most Medium.

**Phase 4 triage matrix.** Assumptions aren't stress-tested in random order. Impact (how many chains depend on it) × likelihood (how hidden it is) determines the test order. High-impact × high-likelihood first.

**Two invocation modes.** Explicit call (`/logic-audit`) runs the full 6-phase audit. Proactive trigger (post-edit) runs a focused audit — changed artifacts + immediate dependents, three checks, no phase 3/4 unless CRITICAL surfaces. The right depth for the right context.

**Differential mode.** Give it a prior audit report alongside the current artifacts and it fingerprint-matches every old finding: PERSISTS / SHIFTED / RE-VERIFY / RESOLVED / RESOLVED-DELETED. Renames, moved content, and deleted artifacts are all handled explicitly.

**"Fix these first."** The report leads with a top-3 actionable summary before the full findings list. All CRITICALs appear there. No hunting through a wall of structured text to find what actually matters.

---

## Output example

```
Mode: full. Authority: spec > code > tests.
Artifacts: 3. Check order: 2.5, 2.1, 2.7, 2.3.
Findings: 1 CRITICAL · 3 HIGH · 0 MINOR.
Assumptions: 3 extracted · 2 tested (67%) · A3 skipped: 0 chains depend on it.
Self-audit: 0 dropped · 0 reclassified.

## Fix these first
1. C1 — auth.py raises ValueError; spec says return None; all error-path tests are wrong
2. H2 — ERR_EXPIRED not implemented; expired tokens fall through to wrong error path
3. H3 — no caller-level ValueError handler; unhandled exception will propagate

## CRITICAL
[C1] contradiction  auth.py:34 vs spec.md:14
  "raise ValueError("invalid token")"  [v: grep "raise" auth.py → line 34]
  "returns None on invalid token"      [v: read spec.md:14 → confirmed]
  Why: test suite written against spec; code raises — all error-path tests silently wrong.
  Evidence: Direct. Confidence: High. Fix: change auth.py to return None.

## OK
✓ 2.1 Reference resolution — spec §3 exists, all codes listed.
  How checked: read spec.md §3; grepped auth.py for each code.
```

---

## Install

```bash
mkdir -p ~/.claude/skills/logic-audit
cp SKILL.md ~/.claude/skills/logic-audit/SKILL.md
```

Then restart Claude Code (or reload skills).

---

## Usage

**Explicit:**
```
/logic-audit spec.md auth.py test_auth.py
```

**Natural language triggers** (auto-detected):
- "does this spec match the implementation?"
- "check if the API docs match what the code actually returns"
- "are these consistent?"
- "do these three contracts hang together?"
- "I just rewrote this module, make sure the docs and tests still hold"
- "does this analysis match the dataset?"

**Proactive** — runs automatically after you generate or heavily edit a set of related artifacts.

---

## Versioning

| Version | What changed |
|---------|-------------|
| v1.4 | Invocation modes, authority field, full-sweep scope defined, coverage gate, "Fix these first" |
| v1.3 | Phase 3 depth limit, mutation tracking spec, large artifact strategy, 3-level Phase 4 likelihood |
| v1.2 | `[v:]` structural gate, worked example, per-check bounds, Phase 4 triage matrix, differential fingerprints |
| v1.1 | Evidence grading with hard ceilings, phase cross-feeding, OK method trails |
| v1.0 | Initial release |
