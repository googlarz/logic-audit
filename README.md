# logic-audit

Cross-artifact logic and consistency auditor for Claude Code. Give it any set of related files — code + tests + docs, spec + implementation, prompt + output, data + analysis + chart — and it finds where they don't hang together.

Not a linter. Not a code reviewer. It finds the bugs that only exist *between* artifacts.

---

## The problem it solves

Most tools check one file at a time. But the nastiest bugs live in the gaps between files — contradictions, broken references, names that drift, numbers that don't add up across documents.

**Technical**
- The spec says `return None` on failure. The code `raise`s. The tests were written against the spec — they all pass, all wrong.
- API spec says the endpoint returns `{ "status": "ok", "data": [...] }`. Implementation returns `{ "success": true, "result": [...] }`. Client checks `status === "ok"` — always fails silently.
- Config says `max_retries=3`. Implementation reads `max_retry` (typo). Silent default kicks in.
- Changelog says field `user_id` removed in v2.3. Migration script still references it. One of them is wrong.

**Legal / contracts**
- Contract A references Contract B as the "governing agreement". Contract B references Contract A. Circular — neither governs.
- Amendment says "as defined in Section 4.2". Section 4.2 defines something different than what the amendment uses it for.
- NDA says non-disclosure lasts 2 years after termination. Employment contract says 1 year. Which governs?

**HR / employment**
- Offer letter says start date March 1. Contract says March 15. Onboarding checklist says "send laptop 2 weeks before start date" — which date does that mean?
- Offer letter says "Senior Engineer". Contract says "Engineer II". Org chart says "Lead Engineer". Three names, one person, zero explanation.

**Finance**
- Invoice says payment due 30 days from delivery. Contract defines "delivery" differently than the delivery note does. Overdue or not depends on which definition applies — and they contradict.
- Q3 report says revenue €2.4M. Board presentation the same week says €2.1M. Neither flags a revision.
- Balance sheet lists an asset acquired in 2021. Depreciation schedule starts in 2023. Two missing years.

**Research / medical**
- Study says N=142 participants. Results table has 139 rows. Discussion says "all 142 completed the protocol."
- Patient record says allergy: penicillin. Discharge summary prescribes amoxicillin (a penicillin-class antibiotic).
- Trial protocol says primary endpoint at 12 weeks. Results section reports 10-week data as the primary outcome.

Logic-audit finds these by treating your document set as a system and checking it as a whole — not reading each file in isolation.

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

---

## License

[Custom](LICENSE) — personal and OSS use free with attribution. Commercial use free but requires a one-time email notification to [googlarz@gmail.com](mailto:googlarz@gmail.com) (company + use case). No payment, just acknowledgment.
