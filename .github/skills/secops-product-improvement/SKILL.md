---
name: secops-product-improvement
description: "Use when improving this SecOps product in VS Code Copilot: security hardening, detection quality, reliability, release readiness, architecture, API validation, performance, or launch documentation."
---

# SecOps Product Improvement

Use this skill when working on this repository in VS Code Copilot.

## Goal

Improve the product with a repeatable Copilot-native workflow that prioritizes security, detection quality, operational reliability, and launch readiness.

## Preferred Agent Set

1. `engineering-security-engineer.md`
2. `engineering-threat-detection-engineer.md`
3. `engineering-devops-automator.md`
4. `engineering-sre.md`
5. `engineering-backend-architect.md`
6. `engineering-software-architect.md`
7. `engineering-ai-engineer.md`
8. `engineering-data-engineer.md`
9. `engineering-code-reviewer.md`
10. `testing-api-tester.md`
11. `testing-performance-benchmarker.md`
12. `testing-reality-checker.md`
13. `engineering-technical-writer.md`
14. `product-manager.md`
15. `engineering-incident-response-commander.md`

## Execution Order

1. Frame the change with `product-manager.md` when the request affects roadmap, packaging, pricing, launch scope, or user value.
2. Use `engineering-software-architect.md` and `engineering-backend-architect.md` for structural changes, integrations, schema changes, and platform boundaries.
3. Use `engineering-security-engineer.md` first for any security-sensitive code, secrets handling, subprocess usage, auth, or supply-chain concerns.
4. Use `engineering-threat-detection-engineer.md` for detection logic, ATT&CK mapping, telemetry coverage, and rule tuning.
5. Use `engineering-ai-engineer.md` and `engineering-data-engineer.md` for dataset generation, evaluation quality, pipelines, and model-assisted analysis.
6. Use `engineering-devops-automator.md` and `engineering-sre.md` for CI/CD, Docker, reliability, observability, and release automation.
7. Use `testing-api-tester.md`, `testing-performance-benchmarker.md`, and `testing-reality-checker.md` as final gates before calling a change launch-ready.
8. Use `engineering-code-reviewer.md` for focused defect/risk review after implementation.
9. Use `engineering-technical-writer.md` to update README, launch docs, and operator-facing workflows.
10. Use `engineering-incident-response-commander.md` when preparing runbooks, incident workflows, or post-incident improvements.

## Default Workflow

1. Inspect existing code and docs before proposing changes.
2. Prefer fixing the root cause rather than patching symptoms.
3. Make small, focused edits that preserve the current public API unless the task requires change.
4. Validate with the narrowest relevant checks first, then broader checks if needed.
5. Call out launch blockers explicitly: security gaps, missing tests, missing telemetry, or brittle release steps.

## Copilot-Specific Notes

- Repo-local agents are stored in `.github/agents/`.
- This skill is repo-local and intended for VS Code Copilot, not Antigravity.
- When asking Copilot for help, reference the exact role you want, for example: `Use engineering-security-engineer.md to review subprocess and file handling risks in this repo.`
