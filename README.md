# logic-audit

A Claude Code skill that audits any set of artifacts for logic and consistency failures — not within a single file, but *across* them.

## What it does

Give it any collection of related artifacts — code + tests + docs, spec + implementation, contract + emails, prompt + output, dataset + analysis + chart, design + ADR + PR — and it finds where they don't hang together.

Five phases:

| Phase | Mode | What happens |
|-------|------|-------------|
| 0 — Scope | Setup | State relationships, known gaps, out-of-scope. Hard-stop only for scope-defining ambiguity; everything else is a bounded best-effort run. |
| 1 — Inventory | Passive | List every artifact. Extract hidden assumptions (structural, temporal, relational, domain). |
| 2 — Checks | Passive | 10 cross-artifact checks: reference resolution, identity drift, quantifier consistency, causal ordering, input/output coherence, structural shape, contradictions, boundary drift, self-reference, realism. |
| 3 — Inference chains | Passive→Active | Trace multi-hop dependency chains backward from key claims. Find snap points — where a chain assumes something not established by its inputs. |
| 4 — Counterfactual stress test | Active | Take Phase 1 assumptions and Phase 3 snap points. Ask: *if this were false, what else breaks?* Attack only what's actually there. |
| 5 — Report | Output | Structured findings with evidence grading, confidence propagation, and method trails on clean checks. |

## What makes it different

**Evidence grading with hard ceilings.** Every finding is typed as Direct, Inferred, or Circumstantial — and confidence cannot exceed the ceiling for that type. High confidence requires Direct evidence.

**Two finding schemas.** Contradiction findings cite both sides. Absence findings (snap points, missing handlers, unestablished preconditions, counterfactual gaps) use `claim + absent + impact` — no fabricated opposing quote required.

**Phases talk to each other.** Phase 2 findings seed Phase 3 chain tracing. Phase 3 snap points seed Phase 4 stress tests. This is how multi-hop bugs get caught — the ones invisible when you check artifacts pairwise.

**OK findings carry method.** "Reference resolution passed" is meaningless without knowing how thoroughly you checked. Every passing check requires a "How checked" note.

**Confidence propagates.** A finding that depends on a Medium finding is at most Medium. A chain with one Circumstantial link is at most Low. Dependency chains are recorded in the report.

## Install

```bash
# As a user skill (invoke with /logic-audit)
cp SKILL.md ~/.claude/skills/logic-audit/SKILL.md
```

## Usage

```
/logic-audit <describe your artifact set or just paste the files>
```

Triggers automatically on phrases like "does this make sense?", "are these consistent?", "check if everything adds up", "verify this looks right".

## Example triggers

- "Does this spec match the implementation?"
- "Check if the API docs match what the code actually returns"
- "These three contracts reference each other — do they hang together?"
- "I just rewrote this module, make sure the docs and tests still hold"
- "Does this analysis match the dataset?"
