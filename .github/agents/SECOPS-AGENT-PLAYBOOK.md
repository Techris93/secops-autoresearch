# SecOps Agent Playbook

This repository now includes a curated agent pack in `.github/agents/`.

## Selected Agents

1. engineering-security-engineer.md
2. engineering-threat-detection-engineer.md
3. engineering-incident-response-commander.md
4. engineering-devops-automator.md
5. engineering-sre.md
6. engineering-backend-architect.md
7. engineering-software-architect.md
8. engineering-ai-engineer.md
9. engineering-data-engineer.md
10. engineering-code-reviewer.md
11. testing-api-tester.md
12. testing-performance-benchmarker.md
13. testing-reality-checker.md
14. engineering-technical-writer.md
15. product-manager.md

## Operating Sequence For This Product

1. Product framing: product-manager.md
2. Architecture pass: engineering-software-architect.md + engineering-backend-architect.md
3. Security implementation: engineering-security-engineer.md
4. Detection quality: engineering-threat-detection-engineer.md
5. Data and pipelines: engineering-data-engineer.md + engineering-ai-engineer.md
6. CI/CD and reliability: engineering-devops-automator.md + engineering-sre.md
7. Validation gates: testing-api-tester.md + testing-performance-benchmarker.md + testing-reality-checker.md
8. Incident readiness: engineering-incident-response-commander.md
9. Final hardening review: engineering-code-reviewer.md
10. Documentation and launch comms: engineering-technical-writer.md

## Suggested Weekly Cadence

1. Monday: product-manager.md + engineering-software-architect.md
2. Tuesday: engineering-security-engineer.md + engineering-threat-detection-engineer.md
3. Wednesday: engineering-data-engineer.md + engineering-ai-engineer.md
4. Thursday: engineering-devops-automator.md + engineering-sre.md
5. Friday: testing-api-tester.md + testing-performance-benchmarker.md + testing-reality-checker.md + engineering-code-reviewer.md

## Notes

- This workspace uses VS Code Copilot, so the active repo-local agents live in `.github/agents/`.
- Global Copilot install is available at `~/.github/agents` and `~/.copilot/agents` for reuse across workspaces.
- To use one of these in Copilot Chat, reference the agent by role and task, or open the matching file in `.github/agents/` for the exact prompt shape.
- To refresh from upstream, pull `~/tools/agency-agents` and re-copy updated agent files.
