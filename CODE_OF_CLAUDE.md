# CODE_OF_CLAUDE.md

This file defines the conventions and expectations for AI-assisted coding in agent-eval.

## AI Agent Conventions

### When AI agents (Claude, Codex, etc.) work on this repository:

1. **Follow the existing patterns** — Read existing code before writing new code. Match the style, structure, and conventions already present. This is a documentation-first project with static HTML docs.

2. **Write tests first** — Every new feature or bug fix must include tests. Target ≥80% coverage if code is added.

3. **Run the full CI locally before pushing** — Execute:
   ```bash
   # For docs validation
   test -f docs/index.html
   grep -q "<!DOCTYPE html>" docs/index.html
   ```

4. **Update documentation** — If you change behavior, update:
   - `CHANGELOG.md` (under `[Unreleased]`)
   - `docs/index.html` for user-facing documentation
   - README.md for project overview

5. **Use conventional commits** — Prefix commits with:
   - `feat:` new feature
   - `fix:` bug fix
   - `docs:` documentation only
   - `refactor:` code change that neither fixes a bug nor adds a feature
   - `test:` adding or modifying tests
   - `chore:` maintenance (deps, config, etc.)

6. **Security first** — Never commit secrets. Use environment variables for configuration. Run security scans (trivy) before merging.

7. **Documentation standards** — The docs site is the primary deliverable:
   - Validate HTML structure
   - Keep ORCID (0009-0009-8515-2727) in footer
   - Maintain Apache 2.0 license header

8. **No silent failures** — All errors must be logged and surfaced appropriately.

## Code Review Checklist for AI Contributions

- [ ] Documentation updated (docs/index.html, README.md)
- [ ] CHANGELOG.md updated
- [ ] CI passes (docs validation, trivy scan)
- [ ] No hardcoded secrets
- [ ] Conventional commit messages

## Prohibited Patterns

- ❌ Hardcoded paths, URLs, or credentials
- ❌ Skipping CI to "make it pass"
- ❌ Modifying generated files
- ❌ Committing directly to `main` (use PRs)

## Escalation

If an AI agent encounters ambiguity or conflicting requirements:
1. Stop and ask the human maintainer
2. Document the question in the PR description
3. Do not guess — clarify first

---

**ORCID**: 0009-0009-8515-2727 (Emir Perla)
**Maintainer**: We Do Care Global