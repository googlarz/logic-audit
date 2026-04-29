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
version: 3.0
---

# Logic & Consistency Audit — v3

Adversarial cross-artifact auditor. Given any set of artifacts, find where
they contradict each other, where references don't resolve, where the causal
order breaks, where inference chains snap, and where hidden assumptions are
violated.

Domain-agnostic: code + tests + docs, spec + implementation, contract + emails,
prompt + output + ground truth, dataset + analysis + chart, design + ADR + PR.

The skill has five phases. Phases 1–3 are passive (scan and map). Phases 4–5
are active (synthesize and attack). Don't skip the active phases — that's
where the real bugs hide.

Findings have two schemas depending on type:

**Contradiction finding** (two artifacts say opposite things):
- Quoted value A + quoted value B — both sides must be cited
- Exact artifact(s) and location(s)
- Severity: CRITICAL / HIGH / MINOR
- Evidence type: Direct / Inferred / Circumstantial (see §Evidence grading)
- Confidence: High / Medium / Low — capped by evidence type and depends-on chain
- Depends-on: [finding IDs this finding rests on, if any]
- Suggested fix where one is computable

**Absence finding** (snap point, missing handler, unestablished precondition,
counterfactual gap — Phase 3 and Phase 4 findings are usually this type):
- Quoted assumption or claim that implies something should exist
- What is absent or unhandled — described precisely, not quoted (it isn't there)
- Why the absence matters: what breaks, silently fails, or remains unverified
- Exact artifact(s) and location(s)
- Severity: CRITICAL / HIGH / MINOR
- Evidence type: Inferred or Circumstantial (absence findings are never Direct)
- Confidence: capped by evidence type and depends-on chain
- Depends-on: [finding IDs this finding rests on, if any]
- Suggested fix where one is computable

## Evidence grading

Every finding must state what kind of evidence it rests on. This is not
optional — it determines the confidence ceiling and tells the reader how
hard to act on the finding.

**Direct** — The contradiction is explicit in the artifact text. Two files
literally say opposite things. A count is stated and wrong. A reference
target is absent. No inference required.
→ Confidence ceiling: High.

**Inferred** — The contradiction follows necessarily from what the artifacts
say, but requires a reasoning step. "This function is called with argument X,
and the implementation requires argument X to satisfy invariant Y, but another
artifact establishes that Y does not hold in this context."
→ Confidence ceiling: Medium. State the reasoning step explicitly.

**Circumstantial** — The pattern is suspicious and consistent with an error,
but an innocent explanation exists. Outlier values, naming drift, structural
gaps that could be intentional.
→ Confidence ceiling: Low. State the innocent explanation alongside the
suspicious one. Let the reader decide.

Rule: never assign High confidence to Inferred or Circumstantial evidence.
Never assign Medium confidence to Circumstantial evidence. The ceiling is hard.

---

## Phase 0 — Scope

Before anything else:

1. **Artifact set** — list every artifact with type and role.
2. **Relationships** — what is supposed to be derived from what?
3. **Known gaps** — anything referenced but missing.
4. **Out of scope** — what you will not verify and why.

**Hard-stop only for scope-defining ambiguity** — e.g. you cannot identify
which artifacts are in scope, or the stated relationships contradict each
other before the audit begins. Stop and ask in those cases only.

For all other uncertainty (missing attachments, unresolvable external
references, unclear derivation edges, partial context) — continue with a
bounded best-effort audit. Record every unresolved item under Known gaps
in Phase 0 and in the final report's skipped-checks list. Do not abort a
proactive post-edit audit because some peripheral context is missing.

---

## Phase 1 — Inventory + assumption extraction

For each artifact:

| Artifact | Type | Role | References | Hidden assumptions |
|----------|------|------|------------|-------------------|
| ... | code/doc/data/... | spec/impl/test/... | cites what | see below |

**Extract hidden assumptions.** Every artifact embeds assumptions it doesn't
state. Surface them explicitly before checking anything.

For each artifact, list:
- **Structural assumptions** — "this field is always present", "this list is
  non-empty", "this function is pure", "these IDs are unique".
- **Temporal assumptions** — "this data is current", "this config was applied
  before this service started", "these events are ordered".
- **Relational assumptions** — "this other artifact exists and is correct",
  "this external system behaves as documented".
- **Domain assumptions** — "this date is UTC", "these amounts are in EUR",
  "this name refers to the same entity throughout".

Write them down. They are the target of Phase 4.

---

## Phase 2 — Passive checks

Run every applicable check. State which ones you skipped and why.

### 2.1 Reference resolution

Every pointer must resolve to something that exists and says what's claimed.

- "See §3.2" → does §3.2 exist? Does it say what's described?
- Symbol name in docs → present in code with the same signature?
- "per RFC 7519 §4.1" → does that section actually say what's quoted?
- Attachment / appendix / file reference → exists?
- Ticket / PR / commit reference → consistent across artifacts?

Flag: target missing → HIGH. Target exists but content disagrees → HIGH.
Ambiguous (multiple matching targets) → MINOR.

### 2.2 Identity & equivalence

Same thing, different names. Alias or drift?

- `User` in spec vs `Account` in code — same concept?
- `v2.1` changelog vs `2.1.0` package.json — equivalent?
- Company with/without legal suffix across documents?
- `/users/me` in docs vs `/api/v1/users/me` in code?

Rule: identity must be trivially obvious or stated explicitly. Otherwise flag.

Flag: unexplained drift → HIGH. Trivial form difference with obvious identity
→ MINOR with canonical form suggested.

**Mutation tracking.** When artifact B is explicitly derived from A (a v2 of
a spec, an amended contract, a refactored module), check:
- Is every change from A to B intentional and documented?
- Does B break any contract that A established?
- Do downstream artifacts that depended on A still hold against B?

Flag: undocumented mutation that changes behaviour → HIGH.
Undocumented mutation that changes semantics without changing behaviour → MINOR.

### 2.3 Quantifier & set consistency

- "All X have property Y" → enumerate X, verify Y on each.
- "There are N items" → count.
- "Supports A, B, C" → what's actually wired up?
- "No side effects" → check for I/O, mutations, external calls.

Flag: any set claim that doesn't hold → HIGH.

### 2.4 Causal & temporal ordering

A depends on B → B must exist or happen first.

- Test asserts state X before the action that produces it.
- Spec says "after auth" — code calls it before.
- Log event B timestamped before event A that caused it.
- Workflow step 3 uses output that step 2 doesn't produce.

Build a unified timeline:
```
T0  [artifact]  event
T1  [artifact]  event
```

Flag: causal inversion → HIGH. Missing required intermediate event → HIGH.
Effective date precedes creation without explicit retroactive clause → HIGH.
Period gaps or overlaps → HIGH.

### 2.5 Input / output coherence

Producer and consumer must agree on shape, type, and meaning.

- Function signature vs every caller.
- API docs vs actual response.
- Schema vs sample data.
- Prompt format vs output format.
- Event emitted vs handler expected shape.
- Migration adds column → something reads/writes it?

Flag: mismatch that fails at runtime → CRITICAL. Silent data loss → HIGH.
Cosmetic mismatch → MINOR.

### 2.6 Completeness & structural shape

Two-part check: claimed coverage vs actual, and whether the artifact set
has the shape it claims to have.

**Coverage:**
- Spec has N requirements → implementation covers M?
- Error cases in docs → handler exists for each?
- Dataset claims daily coverage X–Y → gaps?

**Structural shape:**
- "Complete implementation" but which spec sections have zero corresponding
  code? Name them.
- "Comprehensive test suite" but which public API surface has no tests?
- "Full migration" but which schema objects are untouched?
- The gap map is as important as the gap count — name what's missing.

Flag: claimed coverage > actual → HIGH. Orphan artefacts (implementation
without spec, tests without code, docs without feature) → MINOR.

### 2.7 Internal contradiction

Doc A says X, doc B says ¬X.

- README: "port 8080" vs config: `port: 3000`.
- Comment: "returns null on failure" vs code: raises.
- Spec: "max 100" vs validator: `> 1000`.
- ADR: "decided Redis" vs code: Memcached.
- PR: "no breaking changes" vs diff removes public method.

Flag: contradiction → HIGH. CRITICAL if a reader would make a wrong decision
trusting the stated value.

### 2.8 Boundary & edge consistency

- "0-indexed" claimed, code uses 1.
- Inclusive vs exclusive ranges differ across files.
- "Max 100" — enforced as ≤100 or <100?
- Unit drift: ms vs s, KB vs KiB, UTC vs local, decimal vs hex.
- Null/empty/zero treated differently across artifacts.

Flag: boundary drift → HIGH.

### 2.9 Self-reference / output vs claim

- "100% test coverage" vs report: 67%.
- "3 sections" vs document has 5.
- "Generated on date X" vs content references events after X.
- Audit says "all passed" vs body lists failures.
- Output claims to have performed an action not evidenced elsewhere.

Flag: self-contradiction → HIGH. Often CRITICAL — these are the claims
readers trust first.

### 2.10 Realism & smell tests

- Placeholder markers in production artifacts: `TODO`, `FIXME`, `XXX`,
  `lorem ipsum`, `example.com`, `placeholder`, `__REPLACE_ME__`. Use
  word-boundary matching to avoid false positives (`simulation`, `generator`).
- Sequential IDs with unexplained gaps.
- Identical values where variation is expected.
- Zero variance on a metric that should fluctuate.
- Outliers > 3σ without a documented event explaining them.

For domain-specific realism (checksums, legal identifiers, transaction
volumes, currency rates) — apply only with authoritative reference data,
and state that source explicitly.

---

## Phase 3 — Inference chain tracing

Phases 1–2 are pairwise. Phase 3 traces multi-hop chains.

Most real logic bugs aren't "A contradicts B." They're "A is true, A implies
B, B implies C, but C is false — and nobody noticed because they only checked
A against C directly."

**Phase 2 findings seed this phase.** For every HIGH or CRITICAL finding from
Phase 2, ask: what else must be true for this finding to hold? Trace that
dependency backward. Often the finding is a symptom; the root cause is one
hop upstream.

**For each key claim or output in scope:**

1. **Trace the derivation backward.** What does this claim depend on? What
   does each dependency depend on? Build the chain:
   ```
   claim C
   └── requires B  [from artifact X, evidence: Direct]
       └── requires A  [from artifact Y, evidence: Inferred]
           └── requires precondition P  [stated nowhere — gap, Circumstantial]
   ```

2. **Find where the chain snaps.** A link snaps when:
   - A dependency is missing (never established).
   - A dependency holds under condition X but is used in context Y where X
     is not guaranteed.
   - A step introduces an assumption not warranted by its inputs.
   - Two branches of the chain contradict each other before they merge.

3. **Each link carries an evidence type.** The weakest evidence type in the
   chain sets the confidence ceiling for the entire chain finding. A chain
   with one Circumstantial link is at most Low confidence, regardless of how
   solid the other links are.

4. **Report the snap point, not the symptom.** "C is wrong" is a symptom.
   "The chain from A to C assumes P at step B, and P is not established" is
   the diagnosis.

---

## Phase 4 — Counterfactual stress test

Phase 4 is active and adversarial. It has two inputs:
- Assumptions surfaced in Phase 1
- Snap points identified in Phase 3 (these are the highest-value targets —
  a snap point is already a weak link; counterfactual pressure finds whether
  anything else breaks when it gives way)

For each assumption and each snap point, ask:

> **If this were false, what else would have to be false?**

Then check whether the artifact set handles that case.

Examples:
- Assumption: "user is always authenticated before reaching this handler."
  Counterfactual: what if they aren't? Does any artifact handle or document that?
- Assumption: "this config file is loaded before any service starts."
  Counterfactual: what if it's missing or malformed? Do logs, error handlers,
  or docs address this?
- Snap point from Phase 3: "the chain assumes field X is non-null at step B."
  Counterfactual: one artifact marks it optional — which downstream artifacts
  silently break if it's null?

**Evidence type for Phase 4 findings is always Inferred or Circumstantial**
(never Direct — you are reasoning about what would happen, not reading a
contradiction). Assign confidence accordingly.

**This is not hypothetical speculation.** Only flag when:
(a) the assumption or snap point is real (found in Phase 1 or 3), and
(b) falsehood produces an inconsistency visible within the artifact set.

Don't invent scenarios. Attack what's actually there.

---

## Phase 5 — Report

```
# Audit summary
Artifacts: N. Phases run: [list]. Skipped checks: [list with reason].
Findings: X CRITICAL · Y HIGH · Z MINOR.

## CRITICAL
[C1] contradiction  [artifact:location]
  "[quoted A]" vs "[quoted B]"
  Why: [why impossible / always wrong]
  Evidence: Direct. Confidence: High. Depends-on: —. Fix: [if computable]

[C2] absence  [artifact:location]
  Claim: "[quoted assumption that implies X should be handled]"
  Absent: [what is missing — handler / guard / precondition / etc.]
  Impact: [what silently fails or breaks]
  Evidence: Inferred. Confidence: Medium. Depends-on: —. Fix: [if computable]

## HIGH
[H1] contradiction  [artifact:location]
  "[quoted A]" vs "[quoted B]"
  Why: [why wrong or needs explanation]
  Evidence: Inferred — [one-line reasoning step]. Confidence: Medium.
  Depends-on: [C1 if applicable]. Fix: [if computable]

[H2] absence  [artifact:location]
  Claim: "[quoted assumption]"
  Absent: [what is missing]
  Impact: [consequence]
  Evidence: Inferred. Confidence: Medium. Depends-on: —. Fix: [if computable]

## MINOR
[M1] [artifact:location]  [observation]
  Why noteworthy: [...]. Innocent explanation: [...].
  Evidence: Circumstantial. Confidence: Low. Depends-on: —.

## OK
✓ Reference resolution — N/N references resolved.
  How checked: [enumerated all refs / ran grep / traced call graph / ...]
✓ Input/output coherence — all producer/consumer pairs match.
  How checked: [compared function signatures against callers / ...]
✓ Inference chains — N chains traced, all links hold.
  How checked: [traced backward from these N key claims / ...]
✓ [every check run and passed — state method, not just outcome]
✗ [every check skipped — state reason]

## Assumptions register (Phase 1 → Phase 4)
- [artifact]  "[assumption text]"
  Type: Structural/Temporal/Relational/Domain
  Counterfactual tested: [yes — finding [Hx] / yes — holds / no — out of scope]
```

**Confidence propagation rule:** a finding that depends on another finding
inherits the lower of the two confidence scores. A chain with one
Circumstantial link is at most Low confidence. Record `depends-on` so the
reader can trace the full chain.

**OK findings carry method, not just outcome.** "Reference resolution passed"
means nothing without knowing whether you checked 3 references or 300.
"How checked" is required on every OK line — it tells the reader how much
to trust the clean bill of health.

---

## Principles

**Cross-artifact is the point.** Per-artifact findings belong in a linter,
not here. Value comes from what the artifacts say *about each other*.

**Grade your evidence.** Direct, Inferred, Circumstantial — state which one
on every finding. Never assign confidence above the ceiling for that type.

**Phases talk to each other.** Phase 2 findings seed Phase 3 chain tracing.
Phase 3 snap points seed Phase 4 stress tests. Running phases independently
misses the multi-hop bugs.

**Compute, don't eyeball.** Counts, sums, set membership, checksums — run
as code or explicit enumeration. Visual checks miss things.

**Root cause, not symptom.** N artifacts wrong by the same delta = one root
cause. Report it once, at the snap point.

**OK findings need method, not just outcome.** A clean pass is only
meaningful if the reader knows how thoroughly you checked. State how.

**Confidence propagates.** A finding built on a Medium finding is at most
Medium. A chain with one Circumstantial link is at most Low. Record it.

**Silence is ambiguous.** State every check that passed, every check skipped,
every assumption tested, every assumption not tested and why.

**Distinguish intent from error.** Some contradictions are deliberate. Think
before flagging. State the innocent explanation for every Circumstantial finding.

**Find and explain. Don't fix unless asked.**
