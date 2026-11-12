# Pre-Release Consolidation Baseline — agent-eval-next

## Issue Reference
- Issue #2: "Pre-release: original-code consolidation and 10-step completion plan" (open)
- Acceptance: All required tests on exact candidate SHA; no mocked success, undocumented skipped integrations, exposed credentials, missing attribution, or unproven product claims. Preserve donor repositories; adapt selected modules on development branches. No public release or production deployment in this planning task. OmniGuard remains excluded.

## Baseline SHAs (from issue)
| Reference | SHA | Description |
|-----------|-----|-------------|
| Baseline | 754b308 | fix: repair literal newline escapes found by CI |
| Current HEAD | 972dc3f | feat: add lint/typecheck/test CI workflow, SECURITY.md, CODE_OF_CLAUDE.md (#4) |

## Delta
- Commits ahead of baseline (754b308): 19

## Step 1 Status: IN PROGRESS
**Task:** Sačuvati 754b308 baseline, sedam prolaznih testova i source provenance; definisati semantiku success/deny/approval/error.
(Save baseline, 7 passing tests and source provenance; define success/deny/approval/error semantics.)

**Resolution plan:**
1. Save 754b308 as reviewed baseline
2. Document 7 passing unittest tests
3. Document source provenance
4. Define success/deny/approval/error event semantics

## Source Selection (from issue)
| Source | Decision | Reason |
|--------|----------|--------|
| Original agent-eval/agent_eval/__init__.py | Keep | Foundation with documented provenance |
| gemini-mcp-agentic-tools/eval | Candidate | Not yet confirmed benchmark quality |
| Vault telemetry | Candidate | Shared contract candidate |
| Foundation evaluation adapter | Candidate | Shared contract candidate |

## Steps 2–10
Documented in issue #2 body. Not started.

## Verification
- [ ] Baseline documented (this file)
- [ ] Step 1: 754b308 baseline set, 7 tests documented, provenance recorded, semantics defined
- [ ] Steps 2–10 not started
