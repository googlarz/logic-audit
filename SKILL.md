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
version: 5.0
---

# Logic & Consistency Audit — v5

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

Every finding uses one of two schemas. Choose based on what the finding is.

**Contradiction** (two artifacts say opposite things):
```
[ID] contradiction  [artifact:location]
  "[quoted A]"  [v: tool → result]
  "[quoted B]"  [v: tool → result]
  Why: [why impossible or always wrong]
  Evidence: Direct/Inferred/Circumstantial. Confidence: High/Medium/Low.
  Depends-on: [IDs]. Fix: [if computable]
```

**Absence** (missing handler, unestablished precondition, counterfactual gap):
```
[ID] absence  [artifact:location]
  Claim:  "[quoted text that implies something should exist]"  [v: tool → result]
  Absent: [what is missing — described precisely, not quoted]
  Impact: [what silently fails, breaks, or goes unverified]
  Evidence: Inferred/Circumstantial. Confidence: Medium/Low.
  Depends-on: [IDs]. Fix: [if computable]
```

The `[v: tool → result]` tag is **required** on every quoted value in a
Direct-evidence finding. It is the structural enforcement of the verification
gate — without it, the finding cannot be Direct. See §Verification gate.

---

## Evidence grading

State evidence type on every finding. Ceilings are hard — no exceptions.

**Direct** — explicit in the artifact text. No inference required.
→ Ceiling: High. Requires `[v:]` tag on every quoted value.

**Inferred** — follows necessarily from what artifacts say, but requires a
reasoning step. State the step.
→ Ceiling: Medium. `[v:]` tag recommended but not required.

**Circumstantial** — suspicious pattern, but innocent explanation exists.
State the innocent explanation.
→ Ceiling: Low. No `[v:]` required.

Absence findings are always Inferred or Circumstantial — never Direct.
Phase 3 and Phase 4 findings are always Inferred or Circumstantial.

---

## Verification gate

`[v: tool → result]` is a structured inline tag that proves a quoted value
was verified by a tool call, not recalled from memory.

Format: `[v: read:42 → confirmed]` / `[v: grep "returns null" → 1 match auth.py:87]`
/ `[v: count → 7]` / `[v: exec → sum=142.50]`

**Rules:**
- Every Direct-evidence finding must have `[v:]` on every quoted value.
- Without a `[v:]` tag, the finding is Inferred at best — downgrade it.
- The tag must reference a real tool call made during this audit session.
- In Phase 5 self-audit: any `[v:]` tag that doesn't match the actual tool
  result drops the finding entirely.

This makes the verification gate structural, not advisory. You cannot file
a Direct finding without showing the receipt.

---

## Check priority by artifact type

Run Phase 2 checks in this order. High-yield first — don't burn context on
low-yield checks before the ones most likely to find real bugs.

| Primary artifact types | Priority order |
|------------------------|----------------|
| Code + tests | 2.5 → 2.1 → 2.4 → 2.3 → 2.7 → 2.8 → rest |
| Spec + implementation | 2.1 → 2.5 → 2.6 → 2.3 → 2.7 → 2.2 → rest |
| Docs + code | 2.1 → 2.2 → 2.7 → 2.5 → 2.9 → rest |
| Data + analysis + chart | 2.9 → 2.3 → 2.7 → 2.4 → 2.10 → rest |
| Contracts + correspondence | 2.4 → 2.7 → 2.1 → 2.2 → 2.6 → rest |
| Prompt + output | 2.9 → 2.5 → 2.3 → 2.7 → rest |
| Mixed / unknown | 2.7 → 2.1 → 2.5 → 2.4 → 2.9 → rest |

---

## Per-check scope & stop rules

Each Phase 2 check has a scope bound and stopping rule. Exceeding the bound
wastes context. Stopping early means recording the check as partial.

| Check | Scope | Stop when |
|-------|-------|-----------|
| 2.1 Reference resolution | All explicit cross-artifact pointers | All resolved or all failures filed |
| 2.2 Identity & equivalence | Every named entity appearing in ≥2 artifacts | No unexplained drift found in full sweep |
| 2.3 Quantifier & set consistency | Every universal/existential claim ("all", "every", "no", "always", "never", "N items") | ≤20 instances: check all. >20: check first 10 + random 5 + last 5. Stop at 3 violations |
| 2.4 Causal & temporal | All dated/ordered events across artifacts | Full timeline built and checked |
| 2.5 I/O coherence | All producer/consumer pairs at artifact boundaries | All pairs checked or 3 violations found |
| 2.6 Completeness | All requirements/sections in the authoritative artifact | Full gap map produced |
| 2.7 Contradiction | All claims about values, states, behaviour that appear in ≥2 artifacts | Full sweep or 5 contradictions found |
| 2.8 Boundary & edge | All boundary values and unit declarations | Full sweep, flag first instance of each drift type |
| 2.9 Self-reference | All self-describing claims ("N sections", "complete", "all passed") | Full sweep — these are few and high-value |
| 2.10 Realism | Placeholder scan + statistical checks | Full scan for placeholders; stats only if ≥20 data points |

If context budget forces an early stop, record: `2.X partial — checked N/M [units], stopped: context budget`.

**Large artifact strategy (single file >500 lines):**
Do not read the entire file into context. Instead:
1. Read the header/imports/exports section (first ~30 lines) to understand shape.
2. For each check, use targeted grep/search rather than full reads.
3. Read specific line ranges only when a grep match needs context (±10 lines).
4. If a check genuinely requires full-file reads (e.g. completeness), record
   it as `⚠ partial` citing the file size and what was sampled.

---

## Differential mode

Activated automatically when a previous audit report is in scope alongside
the current artifacts.

**Matching algorithm:**

1. For each finding in the prior report, extract its **fingerprint**:
   `(normalized_artifact_path, normalized_quoted_content_or_claim)`
   - Normalize path: strip leading `./`, lowercase, collapse `//`.
   - Normalize content: strip whitespace, lowercase.

2. Search the current artifact set for each fingerprint:
   - **Exact match** → PERSISTS (same artifact, same content).
   - **Content matches, path changed** → SHIFTED (artifact renamed/moved).
     Re-verify the finding at the new location.
   - **Content no longer present at cited location** → RE-VERIFY (artifact
     changed). Re-run the specific check against the new content. Outcome:
     RESOLVED (problem fixed) or PERSISTS (still present, possibly shifted
     in the same file) or SHIFTED (content moved to a different artifact).
   - **No match anywhere** → RESOLVED (tentative — confirm the artifact
     still exists; if artifact deleted, mark RESOLVED-DELETED).

3. Run all phases on the full artifact set, but:
   - PERSISTS findings: skip re-verification unless severity is CRITICAL.
   - RESOLVED findings: confirm resolution with one tool call, then close.
   - NEW findings get the NEW tag in the summary.

4. In the report summary: `NEW: X · PERSISTS: Y · RESOLVED: Z · SHIFTED: W`

---

## Phase 0 — Scope

1. **Artifact set** — list every artifact with type and role.
2. **Relationships** — what is derived from what?
3. **Known gaps** — anything referenced but missing.
4. **Out of scope** — what you will not verify and why.
5. **Mode** — full / differential / focused (see below).
6. **Authority** — when two artifacts contradict, which is ground truth?
   State the authority order explicitly (e.g. "spec > code > tests").
   If authority cannot be determined, record "authority unknown" under Known
   gaps and flag both sides of every contradiction without declaring a winner.

**Invocation mode:**

- **Explicit** (`/logic-audit` called directly, or user asks to check/audit):
  Full 6-phase audit across all provided artifacts.

- **Proactive** (triggered after you generated or heavily edited artifacts):
  Focused audit — scope = changed artifacts + their immediate dependents only.
  Run phases 1, 2 (checks 2.1 + 2.5 + 2.7 only), and 5. Skip phases 3 and 4
  unless a CRITICAL finding surfaces in phase 2. State "Mode: proactive" in
  the report header.

**Hard-stop only for scope-defining ambiguity** — you cannot identify which
artifacts are in scope, or stated relationships contradict each other before
the audit begins.

For all other uncertainty — continue with bounded best-effort. Record every
unresolved item under Known gaps.

---

## Phase 1 — Inventory + assumption extraction

| Artifact | Type | Role | References | Hidden assumptions |
|----------|------|------|------------|-------------------|
| ... | code/doc/data/... | spec/impl/test/... | cites what | see below |

**Extract hidden assumptions** for each artifact:
- **Structural** — "this field is always present", "IDs are unique", "function is pure".
- **Temporal** — "data is current", "config loaded before service starts".
- **Relational** — "this other artifact exists and is correct".
- **Domain** — "dates are UTC", "amounts are EUR", "name is same entity throughout".

Record in the Assumptions register. Count them. They are the Phase 4 budget.

**Coverage gate:** before Phase 5, compute T/N where T = assumptions tested
and N = total extracted. If T/N < 80% and untested assumptions include any
with impact ≥1 chain: state explicitly which ones were skipped and why
(budget / out-of-scope / no chains depend on it). Skipping without recording
is not permitted — the gap must be visible in the report.

---

## Phase 2 — Passive checks

Run in priority order from §Check priority table. Apply §Scope & stop rules.
State every check run, every check skipped, every check partial.

### 2.1 Reference resolution
Every pointer resolves to something that exists and says what's claimed.
**Tool gate:** look up every reference. Do not file from memory.
Flag: missing → HIGH. Disagrees → HIGH. Ambiguous → MINOR.

### 2.2 Identity & equivalence
Same thing, different names. Alias or drift? Identity must be trivially
obvious or explicitly stated.

**Full sweep scope:** every named entity (person, system, identifier, concept,
value) that appears in ≥2 artifacts. Build an entity list in Phase 1 —
sweep = verifying every item on that list.

**Mutation tracking:** when B derives from A (e.g. interface → implementation,
spec claim → code behaviour, config value → runtime effect), identify every
place B diverges from A. For each divergence: is it documented? Does every
downstream artifact that depends on A's version still hold?

To find mutations: diff the canonical claim in A against every downstream use
in B with grep/read. A mutation is behaviour-changing if it changes:
type, range, nullability, ordering guarantee, error behaviour, or cardinality.
Cosmetic differences (naming, formatting) are not mutations.

Flag: unexplained drift → HIGH. Undocumented behaviour change → HIGH.

### 2.3 Quantifier & set consistency
"All X have Y" → enumerate X, verify Y. Counts → compute with tool.
**Tool gate:** counts and enumerations must be computed, not estimated.
Flag: set claim that doesn't hold → HIGH.

### 2.4 Causal & temporal ordering
Build unified timeline. Flag inversions, gaps, undocumented retroactivity.
Flag: inversion → HIGH. Missing required event → HIGH.

### 2.5 Input / output coherence
Producer/consumer pairs agree on shape, type, meaning.
**Tool gate:** check callers by grep or AST, not recall.
Flag: runtime failure → CRITICAL. Silent data loss → HIGH. Cosmetic → MINOR.

### 2.6 Completeness & structural shape
Coverage + gap map. Name every gap, not just the count.
Flag: claimed > actual → HIGH. Orphans → MINOR.

### 2.7 Internal contradiction
Doc A says X, doc B says ¬X.

**Full sweep scope:** every claim about a value, state, or behaviour that
appears in ≥2 artifacts. Build a claims list from Phase 1 inventory — sweep
= cross-checking every multi-artifact claim against every other artifact that
references the same entity. One pass per claim, not per artifact pair.

Flag: contradiction → HIGH. CRITICAL if reader would act incorrectly on it.

### 2.8 Boundary & edge consistency
Off-by-ones, inclusive/exclusive drift, unit drift, null/zero inconsistency.
Flag: boundary drift → HIGH.

### 2.9 Self-reference / output vs claim
Artifact's claims about itself. These are what readers trust first.
Flag: self-contradiction → HIGH / CRITICAL.

### 2.10 Realism & smell tests
Placeholders (word-boundary match), zero-variance series, sequential ID gaps,
outliers >3σ. Domain-specific realism only with a named authoritative source.

---

## Phase 2.5 — Confidence calibration checkpoint

Before Phase 3:
1. Every High-confidence finding: has `[v:]` tag? Has Direct evidence? Downgrade if not.
2. Every Direct-evidence finding: is there an inferential step hiding in the "why"? Reclassify as Inferred if so.
3. Every CRITICAL finding: genuinely impossible/always-wrong, not just usually wrong? Downgrade to HIGH if uncertain.

Miscalibrated findings propagate wrong confidence into Phase 3 chains.

---

## Phase 3 — Inference chain tracing

Phase 2 HIGH/CRITICAL findings seed this phase. For each, ask: what else must
be true for this to hold? Trace backward to find the root, not the symptom.

```
claim C
└── requires B  [artifact X, Direct — v: read:42 → confirmed]
    └── requires A  [artifact Y, Inferred — reasoning: ...]
        └── requires P  [not found — Circumstantial gap]  ← snap point
```

Chain snaps when: dependency missing; holds under X, used in Y where X not
guaranteed; introduces unwarranted assumption; two branches contradict.

**Depth limit:** stop tracing a chain when any of these is true:
- You reach an artifact boundary (the dependency is in an artifact not in scope).
- The chain has reached 5 hops without a snap point — record as "no snap found
  within 5 hops" and move on.
- The next required dependency is a universal framework or language guarantee
  (e.g. "Python integers don't overflow") — treat as terminal, not a gap.
- The snap point is already captured by an existing Phase 2 or Phase 3 finding.

Record all snap points found. If a chain produces no snap point after full
depth, record it as a "clean chain" in the Assumptions register.

Weakest evidence type in chain sets ceiling for the whole finding.
Report snap point, not symptom.

---

## Phase 4 — Counterfactual stress test

**Inputs:** Phase 1 assumptions + Phase 3 snap points (highest priority).

**Triage by impact × likelihood** before testing:

| | Low likelihood of being false | Medium likelihood | High likelihood of being false |
|---|---|---|---|
| **High impact** (≥3 chains depend on it) | Test third | Test second | Test first |
| **Low impact** (<3 chains depend on it) | Skip | Test last | Test third |

- **Impact** = number of Phase 3 chains that depend on this assumption.
  High = ≥3 dependent chains or a CRITICAL finding depends on it.
  Low = <3 chains and no CRITICAL dependency.

- **Likelihood of being false** — score each assumption:
  - **Low**: explicitly guaranteed in an artifact in scope (e.g. a contract clause,
    an assert statement, a type annotation) AND no Phase 2 signals nearby.
  - **Medium**: partially covered (implied by context, or guaranteed in one artifact
    but not enforced in another) OR a MINOR Phase 2 finding in the same area.
  - **High**: completely implicit — no artifact covers it — OR an existing Phase 2
    finding already hints at a violation (a smell-test hit, identity drift nearby,
    a MINOR finding in the same area that could explain the assumption being wrong).

Work high-impact × high-likelihood first. Record the triage score for each
assumption tested. Stop when budget is exhausted; name untested assumptions.

For each: **if this were false, what else would have to be false?**
Only flag when the assumption is real (Phase 1/3) and falsehood produces
a visible inconsistency in the artifact set. Don't invent scenarios.

Evidence: always Inferred or Circumstantial. Never Direct.

---

## Phase 5 — Self-audit + report

### 5.1 Self-audit (mandatory before publishing)

For every finding in the draft:

1. Re-read cited location with a tool call. Confirm every quoted value
   character-for-character. Mismatch → drop the finding.
2. Confirm artifact and line number exist. Hallucinated location → drop.
3. Confirm `[v:]` tags match actual tool results. Mismatch → drop or downgrade.
4. Re-check evidence classification per §Phase 2.5 rules.
5. Propagate any drops/downgrades through depends-on chains.

Drop = basis was wrong. Downgrade = basis real, classification wrong.
Record counts: `Self-audit: P dropped, Q reclassified`.

### 5.2 Report

```
# Audit summary
Mode: [full / proactive / differential — prior report: YYYY-MM-DD]
Artifacts: N. Check order: [2.X, 2.Y, ...]. Partial/skipped: [list + reason].
Findings: C CRITICAL · H HIGH · M MINOR.
Assumptions: N extracted · T tested (T/N = X%) · skipped: [list + reason].
Self-audit: P dropped · Q reclassified.
[Differential only] NEW: X · PERSISTS: Y · RESOLVED: Z · SHIFTED: W.

## Fix these first
1. [ID] — [one-line description of the highest-priority finding]
2. [ID] — [second]
3. [ID] — [third]
(CRITICAL findings always appear here. Fill remaining slots with highest-impact HIGH findings.
Omit this section only if there are zero CRITICAL and zero HIGH findings.)

## CRITICAL
[C1] contradiction  [artifact:location]
  "[quoted A]"  [v: read:42 → confirmed]
  "[quoted B]"  [v: read:17 → confirmed]
  Why: [why impossible / always wrong]
  Evidence: Direct. Confidence: High. Depends-on: —. Fix: [if computable]

[C2] absence  [artifact:location]
  Claim:  "[quoted text implying X should exist]"  [v: read:8 → confirmed]
  Absent: [what is missing]
  Impact: [what breaks]
  Evidence: Inferred — [reasoning step]. Confidence: Medium.
  Depends-on: —. Fix: [if computable]

## HIGH
[H1] contradiction  [artifact:location]
  "[quoted A]"  [v: grep → 1 match]
  "[quoted B]"  [v: read:33 → confirmed]
  Why: [...]
  Evidence: Inferred — [step]. Confidence: Medium.
  Depends-on: [C1]. Fix: [if computable]

## MINOR
[M1] [artifact:location]  [observation]
  Innocent explanation: [...].
  Evidence: Circumstantial. Confidence: Low. Depends-on: —.

## OK
✓ [check] — [outcome].  How checked: [tool + scope]
✗ [check] — skipped: [reason]
⚠ [check] — partial: checked N/M [units], stopped: [reason]

## Assumptions register
[A1]  [artifact]  "[assumption]"  Type: Structural/Temporal/Relational/Domain
  Impact: N chains.  Likelihood: High/Low.  Triage score: [H×H / H×L / L×H / L×L]
  Tested: [yes → finding Hx / yes → holds / no → budget / no → out of scope]
```

---

## Worked example

Three artifacts: `spec.md`, `auth.py`, `test_auth.py`.

**Phase 0:** scope = spec → impl → tests. No prior report. Full audit.

**Phase 1 inventory:**

| Artifact | Type | Role | References |
|----------|------|------|------------|
| spec.md | Markdown | Requirements | — |
| auth.py | Python | Implementation | spec.md |
| test_auth.py | Python | Tests | auth.py |

Hidden assumptions:
- [A1] auth.py: "token parameter is always a non-empty string" (Structural)
- [A2] test_auth.py: "auth.py returns None on failure, not raises" (Relational)
- [A3] spec.md: "all error paths are enumerated in §3" (Structural)

**Phase 2 (code+tests priority: 2.5 → 2.1 → ...):**

*Check 2.5 — I/O coherence:*
Tool: `grep "def authenticate" auth.py` → `def authenticate(token: str) -> dict | None`
Tool: `grep "authenticate(" test_auth.py` → `result = authenticate("")`
Caller passes empty string; signature accepts `str` but assumption [A1] says
non-empty. Flag [H1].

Tool: `grep "return None" auth.py` → 0 matches
Tool: `grep "raise" auth.py` → `raise ValueError("invalid token")`
Test expects `None` on failure per [A2]; implementation raises. Flag [C1].

*Check 2.1 — References:*
Tool: `grep "§3" auth.py` → `# error codes defined in spec §3`
Tool: read spec.md §3 → section exists, lists 3 error codes.
Tool: grep auth.py for each code → 2 of 3 implemented. Flag [H2].

**Phase 2.5 calibration:** C1 is Direct + tool-verified ✓. H1 is Inferred ✓. H2 is Inferred ✓.

**Phase 3 — chains:**
C1 (raises vs returns None) → test_auth.py was written against the spec, not the code.
Root: spec says "returns None" [v: read spec.md:14 → "returns None on invalid token"],
code raises. C1 is the root, not a symptom.

**Phase 4 — counterfactual:**
[A2] impact=2 chains, likelihood=high (C1 shows it's already false). Score: H×H → test first.
If auth.py raises instead of returning None: test suite fails silently if exceptions
are caught at caller level. No caller in scope — flag as [H3] absence.

**Phase 5 self-audit:** re-read all cited locations. All quotes confirmed. 0 dropped.

**Report:**
```
Mode: full.
Artifacts: 3. Check order: 2.5, 2.1, 2.7, 2.3 (rest skipped: low yield for this set).
Findings: 1 CRITICAL · 3 HIGH · 0 MINOR.
Assumptions: 3 extracted · 2 tested (67%) · A3 skipped: 0 chains depend on it (gate satisfied).
Self-audit: 0 dropped · 0 reclassified.

## Fix these first
1. C1 — auth.py raises ValueError on failure; spec says return None; all error-path tests are wrong
2. H2 — ERR_EXPIRED not implemented; expired tokens fall through to wrong error path
3. H3 — no caller-level handler for ValueError; unhandled exception will propagate

## CRITICAL
[C1] contradiction  auth.py:34 vs spec.md:14
  "raise ValueError("invalid token")"  [v: grep "raise" auth.py → line 34]
  "returns None on invalid token"      [v: read spec.md:14 → confirmed]
  Why: test suite written against spec; code raises — all error-path tests silently wrong.
  Evidence: Direct. Confidence: High. Depends-on: —. Fix: change auth.py to return None.

## HIGH
[H1] absence  auth.py:1
  Claim:  "def authenticate(token: str)"  [v: grep "def authenticate" → line 1]
  Absent: guard for empty string (assumption A1 is implicit, never enforced)
  Impact: authenticate("") reaches token logic with undefined behaviour
  Evidence: Inferred — signature accepts str; empty str is valid str. Confidence: Medium.

[H2] absence  spec.md §3 / auth.py
  Claim:  "# error codes defined in spec §3"  [v: grep "§3" auth.py → line 12]
  Absent: error code ERR_EXPIRED not implemented in auth.py
  Impact: expired tokens fall through to generic invalid-token path, wrong error surfaced
  Evidence: Inferred — spec lists 3 codes, grep finds 2. Confidence: Medium.

[H3] absence  (no artifact — cross-cutting)
  Claim:  A2 falsified: auth.py raises, doesn't return None
  Absent: any caller-level handler for ValueError from authenticate()
  Impact: unhandled exception propagates if caller expects None-check pattern
  Evidence: Inferred — no caller in scope; ValueError not documented. Confidence: Medium.

## OK
✓ 2.1 Reference resolution — spec §3 exists and lists codes.
  How checked: read spec.md §3 directly; grepped auth.py for each code.
✗ 2.6 Completeness — skipped: spec has 1 page, gap map would duplicate H2.
✗ 2.8 Boundary — skipped: no numeric boundaries in scope.

## Assumptions register
[A1] auth.py "token is always non-empty"  Structural  Impact: 1  Likelihood: High  H×H
  Tested: yes → finding H1
[A2] test_auth.py "auth.py returns None on failure"  Relational  Impact: 2  Likelihood: High  H×H
  Tested: yes → C1 (assumption false)
[A3] spec.md "all error paths in §3"  Structural  Impact: 0  Likelihood: Low  L×L
  Tested: no — low dependency, skipped
```

---

## Worked example — differential mode

Same three artifacts, one sprint later. Prior report (above) is in scope.
`auth.py` was refactored: `authenticate()` moved to `auth/validator.py`.
`spec.md` §3 now lists all 4 error codes. `test_auth.py` unchanged.

**Phase 0:** differential mode. Prior report: 2026-04-29.

**Differential matching:**

Prior findings: C1, H1, H2, H3.

- **C1** fingerprint: `(auth.py, raise valueerror("invalid token"))` + `(spec.md, returns none on invalid token)`
  - `auth.py` grep for `raise ValueError` → 0 matches. RE-VERIFY.
  - RE-VERIFY: grep `auth/validator.py` for `raise ValueError` → 1 match.
  - Content found, path changed → **SHIFTED** (auth.py → auth/validator.py). Re-verify the contradiction still holds.
  - `spec.md:14` still reads "returns None" [v: read spec.md:14 → confirmed]. SHIFTED + PERSISTS.

- **H2** fingerprint: `(spec.md, # error codes defined in spec §3)` + absence of ERR_EXPIRED
  - `spec.md` §3 now lists 4 codes [v: read spec.md §3 → 4 codes listed].
  - grep `auth/validator.py` for ERR_EXPIRED → 1 match [v: grep → line 18].
  - All 4 codes now implemented → **RESOLVED**.

- **H1** fingerprint: `(auth.py, def authenticate(token: str))`
  - `auth.py` grep → 0 matches. RE-VERIFY.
  - grep `auth/validator.py` → `def authenticate(token: str)` line 3. **SHIFTED**.
  - Empty-string guard still absent [v: grep "if not token" auth/validator.py → 0 matches]. SHIFTED + PERSISTS.

- **H3** fingerprint: absence, no quoted artifact location.
  - Re-check: grep all files for `authenticate(` call sites → `app.py:42` calls it.
  - grep `app.py` for `except ValueError` → 0 matches [v: grep → 0 matches]. **PERSISTS**.

**Report summary (differential):**
```
NEW: 0 · PERSISTS: 3 (C1-SHIFTED, H1-SHIFTED, H3) · RESOLVED: 1 (H2) · SHIFTED: 2 (C1, H1)
```


**`[v:]` is the gate, not advice.** No tag = no Direct evidence. This is
structural — you cannot file a Direct finding without showing the receipt.

**Self-audit before publishing.** Re-read every cited location. Drop findings
whose quotes don't match. A wrong citation poisons the whole report.

**Triage Phase 4 by impact × likelihood.** A well-established high-dependency
assumption is less interesting than an implicit low-dependency one that hints
at being false. Score before testing.

**Differential matching uses fingerprints.** Match on normalized path +
normalized content. Handle renames, moved content, and deleted artifacts
explicitly — don't assume a prior finding is resolved without checking.

**Per-check scope bounds are hard.** Partial is better than silent
over-coverage. Record partial checks in the report.

**Phases talk to each other.** Phase 2 seeds Phase 3. Phase 3 seeds Phase 4.
Running phases independently misses multi-hop bugs.

**Evidence ceilings are hard.** Direct → High. Inferred → Medium.
Circumstantial → Low. No exceptions.

**Confidence propagates.** Weakest link sets the ceiling for the chain.

**OK findings need method.** State how you checked, not just that you did.

**Root cause, not symptom.** Report the snap point, not the downstream effect.

**Find and explain. Don't fix unless asked.**
