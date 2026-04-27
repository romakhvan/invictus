# Docs QA Architecture Design

## Goal

Reduce navigation chaos in `docs/qa` by replacing the flat `docs/qa/automation/`
layout with a small set of purpose-based sections.

## Problems In Current Structure

- Entry-point docs, platform docs, process docs, and business reference docs are
  mixed in one flat directory.
- The current layout does not match common reader journeys:
  onboarding, framework understanding, platform-specific work, and business
  reference lookup.
- `README.md` acts as a large unordered index instead of a stable navigation
  hub.

## Approved Target Structure

```text
docs/qa/
  README.md

  onboarding/
    README.md
    getting-started.md
    run-tests.md
    ci-cd.md

  architecture/
    README.md
    overview.md
    architecture.md
    test-strategy.md
    best-practices.md
    reporting-allure.md
    debugging.md

  platforms/
    README.md
    backend.md
    backend-tests.md
    web.md
    mobile.md
    mobile-page-states.md

  domain/
    README.md
    test-data.md
    subscriptions.md
    visit-types.md
    webkassa.md

  legacy/
    README.md
    legacy-docs-index.md
```

## Design Principles

- `docs/qa/README.md` is the single entrypoint for QA docs.
- Each section gets its own `README.md` as a local navigation hub.
- Files are grouped by reader intent, not by historical placement.
- Existing document bodies should be preserved where possible; the migration
  should prefer moving and relinking over rewriting.
- Agent-facing references in `docs/ai-agent-rules.md` must point to the new
  entrypoints.

## Migration Plan

1. Create the five target directories and add section `README.md` files.
2. Move existing files from `docs/qa/automation/` into the new sections.
3. Replace the old flat QA `README.md` with a root-level QA hub.
4. Update references across `README.md`, `docs/QUICK_START.md`,
   `docs/mobile_testing_strategy.md`, `docs/ai-agent-rules.md`, and moved docs.
5. Remove the obsolete `docs/qa/automation/` directory once all content is
   relocated.

## Scope Boundaries

- No content refactor beyond navigation and path updates.
- No attempt to consolidate overlapping legacy docs in this change.
- No changes to test code or runtime behavior.

## Verification

- Confirm all expected files exist in the new structure.
- Search the repository for stale `docs/qa/automation` references.
- Spot-check the main hubs and agent rules for correct links.
