# Contributing to logic-audit

A Claude Code skill for adversarial cross-artifact logic and consistency auditing. Contributions welcome.

## Before you start

- Check [open issues](https://github.com/googlarz/logic-audit/issues) and [discussions](https://github.com/googlarz/logic-audit/discussions)
- The skill is intentionally narrow — proposals to expand scope should be discussed first

## What to contribute

- **Audit patterns** — new categories of logical inconsistency worth checking
- **False positive reduction** — cases where the skill over-flags
- **Examples** — real artifacts showing the skill catching a real problem
- **Bug reports** — include the prompt and artifacts you used

## Submitting a PR

1. Fork → branch from `main`
2. Changes to `SKILL.md` must keep the adversarial framing — the skill's value is in rigour, not helpfulness
3. New audit checks must be falsifiable — the agent must be able to determine pass/fail
4. Open the PR with a concrete example of what your change catches (or stops catching)
