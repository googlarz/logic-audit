---
name: logic-audit
description: >
  Cross-artifact logic and consistency audit. Given any set of files, inputs,
  outputs, or claims — code, specs, docs, data, prose, transcripts, logs,
  configs, contracts — find where they don't hang together. Trigger when the
  user asks to verify things "make sense", "are consistent", "add up", "actually
  do what they say", or requests a thorough check of a set of related artifacts.
  Also trigger proactively after generating or heavily editing a set of related
  artifacts before declaring done.
version: 4.0
---

# Logic & Consistency Audit — v4

Adversarial cross-artifact auditor. Given any set of artifacts, find where
they contradict each other, where references don't resolve, where the causal
order breaks, where inference chains snap, and where hidden assumptions are
violated.

Domain-agnostic: code + tests + docs, spec + implementation, contract + emails,
prompt + output + ground truth, dataset + analysis + chart, design + ADR + PR.

Six phases. Phases 0–3 scan and map. Phase 4 attacks. Phase 5 verifies the
report itself before publishing. Don't skip phases — that's where the real
bugs hide.

---

## Finding schemas

Every finding uses one of two schemas:

**Contradiction** (two artifacts say opposite things):
- Quoted value A + quoted value B — both sides cited and tool-verified
- Artifact(s) and exact location(s)
- Severity: CRITICAL / HIGH / MINOR
- Evidence: Direct / Inferred / Circumstantial
- Confidence: capped by evidence type and depends-on chain
- Depends-on: [IDs of findings this rests on]
- Fix: [if computable]

**Absence** (missing handler, unestablished precondition, counterfactual gap):
- Quoted claim or assumption that implies something should exist
- What is absent — described precisely (it isn't there, so it can't be quoted)
- Impact: what silently fails, breaks, or remains unverified
- Artifact(s) and exact location(s)
- Severity: CRITICAL / HIGH / MINOR
- Evidence: Inferred or Circumstantial (absence findings are never Direct)
- Confidence: capped by evidence type and depends-on chain
- Depends-on: [IDs of findings this rests on]
- Fix: [if computable]

---

## Evidence grading

State evidence type on every finding. The ceiling is hard — no exceptions.

**Direct** — explicit in the artifact text. No inference required.
→ Ceiling: High confidence.

**Inferred** — follows necessarily from what the artifacts say, but requires
a reasoning step. State the step.
→ Ceiling: Medium confidence.

**Circumstantial** — pattern is suspicious but an innocent explanation exists.
State the innocent explanation alongside the finding.
→ Ceiling: Low confidence.

Absence findings are always Inferred or Circumstantial — never Direct.
Phase 3 and Phase 4 findings are always Inferred or Circumstantial.

---

## Verification gate

**Every claim that is filed as Direct evidence must be tool-verified before
the finding is written.** This means:

- A quoted value → re-read that exact location with a tool call and confirm
  the quote is accurate character-for-character.
- A count or sum → compute it (code execution or explicit enumeration).
- A reference target → look it up and confirm it exists and says what's claimed.
- A structural claim ("this function has N callers") → grep or trace it.

Visual/recall-based claims are Inferred at best, not Direct. If you cannot
run a tool to verify it, downgrade the evidence type.

This gate applies before filing any finding, and again in Phase 5 self-audit.

---

## Check priority by artifact type

Run Phase 2 checks in priority order for the artifact set. High-yield checks
first — don't burn context on low-yield checks before the ones most likely
to find real bugs.

| Primary artifact types | Priority order |
|------------------------|----------------|
| Code + tests | 2.5 → 2.1 → 2.4 → 2.3 → 2.7 → 2.8 → rest |
| Spec + implementation | 2.1 → 2.5 → 2.6 → 2.3 → 2.7 → 2.2 → rest |
| Docs + code | 2.1 → 2.2 → 2.7 → 2.5 → 2.9 → rest |
| Data + analysis + chart | 2.9 → 2.3 → 2.7 → 2.4 → 2.10 → rest |
| Contracts + correspondence | 2.4 → 2.7 → 2.1 → 2.2 → 2.6 → rest |
| Prompt + output | 2.9 → 2.5 → 2.3 → 2.7 → rest |
| Mixed / unknown | 2.7 → 2.1 → 2.5 → 2.4 → 2.9 → rest |

Stop and record context-budget status after each check. If budget is running
low, complete the current check, record remaining checks as skipped with reason
"context budget", and proceed to Phase 3 with what you have.

---

## Differential mode

If a previous audit report is provided alongside the current artifact set:

1. Load the previous report's findings list.
2. For each previous finding, check: resolved / still present / changed.
3. Run all phases normally but flag each new finding as NEW and each
   resolved finding as RESOLVED in the summary.
4. Skip checks where neither the artifact nor its references changed since
   the previous audit — record as "unchanged since last audit, skipped."

This mode is activated automatically when a previous audit report is in scope.

---

## Phase 0 — Scope

1. **Artifact set** — list every artifact with type and role.
2. **Relationships** — what is derived from what?
3. **Known gaps** — anything referenced but missing.
4. **Out of scope** — what you will not verify and why.
5. **Mode** — full audit or differential? (differential if prior report present)

**Hard-stop only for scope-defining ambiguity** — e.g. you cannot determine
which artifacts are in scope, or stated relationships contradict each other
before the audit begins.

For all other uncertainty — continue with bounded best-effort. Record every
unresolved item under Known gaps. Do not abort a proactive post-edit audit
because some peripheral context is missing.

---

## Phase 1 — Inventory + assumption extraction

For each artifact:

| Artifact | Type | Role | References | Hidden assumptions |
|----------|------|------|------------|-------------------|
| ... | code/doc/data/... | spec/impl/test/... | cites what | see below |

**Extract hidden assumptions** for each artifact:
- **Structural** — "this field is always present", "IDs are unique", "list
  is non-empty", "this function is pure".
- **Temporal** — "this data is current", "config applied before service
  starts", "events are in order".
- **Relational** — "this other artifact exists and is correct", "external
  system behaves as documented".
- **Domain** — "dates are UTC", "amounts are EUR", "this name is the same
  entity throughout".

Record them in the Assumptions register. Count them. They are the budget for
Phase 4.

**Assumption coverage target:** stress-test at least 80% of extracted
assumptions in Phase 4. Record which ones were skipped and why.

---

## Phase 2 — Passive checks

Run in priority order from the §Check priority table. State every check
run, every check skipped, and why.

### 2.1 Reference resolution

Every pointer must resolve to something that exists and says what's claimed.

- "See §3.2" → does §3.2 exist? Does it say what's described?
- Symbol name in docs → present in code with the same signature?
- "per RFC 7519 §4.1" → does that section say what's quoted?
- Attachment / appendix / file → exists?
- Ticket / PR / commit → consistent across artifacts?

**Tool gate:** look up every reference. Do not file a resolution failure from
memory.

Flag: target missing → HIGH. Target exists but content disagrees → HIGH.
Ambiguous → MINOR.

### 2.2 Identity & equivalence

Same thing, different names. Alias or drift?

- `User` in spec vs `Account` in code — same concept?
- `v2.1` changelog vs `2.1.0` package.json — equivalent?
- Company with/without legal suffix across documents?
- `/users/me` in docs vs `/api/v1/users/me` in code?

Rule: identity must be trivially obvious or explicitly stated. Otherwise flag.

Flag: unexplained drift → HIGH. Trivial form difference with obvious identity
→ MINOR with canonical form.

**Mutation tracking.** When B is derived from A (v2 spec, amended contract,
refactored module), check:
- Every change from A to B intentional and documented?
- Does B break any contract A established?
- Do downstream artifacts that depended on A still hold against B?

Flag: undocumented behaviour-changing mutation → HIGH.
Undocumented semantic-only mutation → MINOR.

### 2.3 Quantifier & set consistency

- "All X have property Y" → enumerate X, verify Y on each.
- "There are N items" → count with a tool.
- "Supports A, B, C" → what's actually wired up?
- "No side effects" → check for I/O, mutations, external calls.

**Tool gate:** counts and enumerations must be computed, not estimated.

Flag: any set claim that doesn't hold → HIGH.

### 2.4 Causal & temporal ordering

A depends on B → B must exist or happen first.

Build a unified timeline:
```
T0  [artifact]  event
T1  [artifact]  event
```

Flag: causal inversion → HIGH. Missing required event → HIGH. Effective
date precedes creation without explicit retroactive clause → HIGH. Period
gaps or overlaps → HIGH.

### 2.5 Input / output coherence

Producer and consumer must agree on shape, type, meaning.

- Function signature vs every caller.
- API docs vs actual response.
- Schema vs sample data.
- Event emitted vs handler expected shape.
- Migration adds column → something reads/writes it?

**Tool gate:** check callers by grep or AST, not by recall.

Flag: runtime failure mismatch → CRITICAL. Silent data loss → HIGH.
Cosmetic → MINOR.

### 2.6 Completeness & structural shape

**Coverage:** spec has N requirements → implementation covers M? Name the M.

**Shape:** which spec sections map to zero code? Which public API surface has
no tests? Which schema objects are untouched? The gap map matters as much as
the gap count.

Flag: claimed coverage > actual → HIGH. Orphans (impl without spec, tests
without code) → MINOR.

### 2.7 Internal contradiction

Doc A says X, doc B says ¬X.

- README: "port 8080" vs config: `port: 3000`.
- Comment: "returns null" vs code: raises.
- Spec: "max 100" vs validator: `> 1000`.
- ADR: "decided Redis" vs code: Memcached.

Flag: contradiction → HIGH. CRITICAL if a reader would act incorrectly on
the stated value.

### 2.8 Boundary & edge consistency

- "0-indexed" claimed, code uses 1.
- Inclusive vs exclusive ranges differ across files.
- Unit drift: ms vs s, KB vs KiB, UTC vs local.
- Null/empty/zero treated differently across artifacts.

Flag: boundary drift → HIGH.

### 2.9 Self-reference / output vs claim

- "100% coverage" vs report: 67%.
- "3 sections" vs document has 5.
- "Generated on date X" vs content references events after X.
- Output claims to have performed an action not evidenced elsewhere.

Flag: self-contradiction → HIGH. Often CRITICAL — these are the claims
readers trust first.

### 2.10 Realism & smell tests

- Placeholder markers: `TODO`, `FIXME`, `XXX`, `lorem ipsum`, `example.com`,
  `__REPLACE_ME__`. Word-boundary match only.
- Sequential IDs with unexplained gaps.
- Identical values where variation is expected.
- Zero variance on a metric that should fluctuate.
- Outliers > 3σ without a documented event explaining them.

Domain-specific realism only with authoritative reference data — state source.

---

## Phase 2.5 — Confidence calibration checkpoint

Before proceeding to Phase 3, review all Phase 2 findings:

1. List every finding assigned High confidence. Confirm each has Direct
   evidence and a tool-verified quote. Downgrade any that don't.
2. List every finding assigned Direct evidence. Confirm no inferential step
   is hiding in the "why." Reclassify as Inferred if there is one.
3. List every finding assigned CRITICAL. Confirm it is genuinely impossible
   or always wrong, not just usually wrong. Downgrade to HIGH if uncertain.

This pass happens before chaining — a miscalibrated Phase 2 finding that
seeds Phase 3 will propagate incorrect confidence downstream.

---

## Phase 3 — Inference chain tracing

Phase 2 findings seed this phase. For every HIGH or CRITICAL finding, ask:
what else must be true for this to hold? Trace backward. The finding is often
a symptom; the root cause is one hop upstream.

For each key claim or output:

1. **Trace the derivation backward:**
   ```
   claim C
   └── requires B  [artifact X, Direct — tool-verified]
       └── requires A  [artifact Y, Inferred — reasoning step stated]
           └── requires precondition P  [not found anywhere — Circumstantial gap]
   ```

2. **Find where the chain snaps:**
   - Dependency missing (never established).
   - Dependency holds under condition X, used in context Y where X not guaranteed.
   - Step introduces assumption not warranted by its inputs.
   - Two branches contradict before they merge.

3. **Evidence propagation:** weakest link in the chain sets the ceiling for
   the entire chain finding.

4. **Report snap point, not symptom.** "C is wrong" is a symptom. "Chain
   from A to C assumes P at step B; P is not established" is the diagnosis.

---

## Phase 4 — Counterfactual stress test

Two inputs:
- Assumptions from Phase 1 (target: ≥80% coverage)
- Snap points from Phase 3 (highest priority — already weak links)

For each, ask: **if this were false, what else would have to be false?**
Then check whether the artifact set handles that case.

Prioritize by impact: test assumptions that the most Phase 3 chains depend
on first. Low-dependency assumptions last. Stop when budget is exhausted and
record untested assumptions explicitly.

Evidence type: always Inferred or Circumstantial. Never Direct.

Only flag when:
(a) the assumption or snap point is real (Phase 1 or Phase 3), and
(b) falsehood produces an inconsistency visible in the artifact set.

Don't invent scenarios. Attack what's actually there.

---

## Phase 5 — Self-audit + report

### 5.1 Self-audit (mandatory before publishing)

For every finding in the draft report:

1. **Re-read the cited location** with a tool call. Confirm the quote is
   accurate character-for-character. If it isn't, correct or drop the finding.
2. **Confirm the artifact and line number exist.** A finding that cites a
   non-existent location is a hallucination — drop it.
3. **Re-check evidence classification** against the calibration rules in
   §Phase 2.5. Reclassify if needed.
4. **Re-check depends-on chains** — if a finding's dependency was downgraded
   or dropped in self-audit, propagate the change downstream.

A finding that fails self-audit is removed from the report, not demoted.
A demoted finding had a real basis but wrong classification. A failed
self-audit means the basis itself was wrong.

### 5.2 Report

```
# Audit summary
Mode: [full / differential from report dated ...]
Artifacts: N. Checks run (in order): [list]. Skipped: [list + reason].
Findings: X CRITICAL · Y HIGH · Z MINOR.
Assumptions: N extracted · M tested (M/N = X%) · K skipped [list].
Self-audit: P findings dropped, Q reclassified.

## CRITICAL
[C1] contradiction  [artifact:location]
  "[quoted A]" vs "[quoted B]"
  Why: [why impossible / always wrong]
  Evidence: Direct (tool-verified: [method]). Confidence: High.
  Depends-on: —. Fix: [if computable]

[C2] absence  [artifact:location]
  Claim: "[quoted assumption]"
  Absent: [what is missing]
  Impact: [what breaks]
  Evidence: Inferred — [reasoning step]. Confidence: Medium.
  Depends-on: —. Fix: [if computable]

## HIGH
[H1] contradiction  [artifact:location]
  "[quoted A]" vs "[quoted B]"
  Why: [...]
  Evidence: Inferred — [reasoning step]. Confidence: Medium.
  Depends-on: [C1 if applicable]. Fix: [if computable]

[H2] absence  [artifact:location]
  Claim: "[...]"  Absent: [...]  Impact: [...]
  Evidence: Inferred. Confidence: Medium. Depends-on: —.

## MINOR
[M1] [artifact:location]  [observation]
  Innocent explanation: [...].
  Evidence: Circumstantial. Confidence: Low. Depends-on: —.

## OK
✓ [check name] — [outcome]
  How checked: [tool used / method / scope]
✗ [check name] — skipped: [reason]

## Assumptions register
[A1] [artifact]  "[assumption text]"  Type: Structural/Temporal/Relational/Domain
  Tested: [yes → finding Hx / yes → holds / no → budget / no → out of scope]
```

---

## Principles

**Tool-verify before filing.** Any claim filed as Direct evidence must have
a tool call that confirmed it. Recall is Inferred at best.

**Self-audit before publishing.** Re-read every cited location. Drop any
finding whose quote doesn't match what's there. A wrong citation poisons
the whole report.

**Phases talk to each other.** Phase 2 seeds Phase 3. Phase 3 seeds Phase 4.
Running phases independently misses multi-hop bugs.

**Prioritize by artifact type.** Run high-yield checks first. State the
order you used.

**Differential when possible.** Don't re-audit unchanged artifacts. Track
what's new, resolved, and changed.

**Assumption coverage is a metric.** Report it. 3/17 tested is not the same
as 15/17.

**Evidence ceilings are hard.** Direct → High. Inferred → Medium.
Circumstantial → Low. No exceptions.

**Confidence propagates.** Weakest link sets the ceiling for the chain.

**OK findings need method.** State how you checked, not just that you did.

**Silence is ambiguous.** Every check run, every check skipped, every
assumption tested, every assumption not tested — all stated explicitly.

**Root cause, not symptom.** Report the snap point, not the downstream effect.

**Find and explain. Don't fix unless asked.**
