# OTCM-150190 — OM-I-3015: split the EasyPost tracker sync onto its own feature flag
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-150190
- **RICE**: OM-I-3015
- **Repos**: monocle_integrations
- **Status** (as of 2026-10-22): PR open, awaiting review
- **Plan**: none (no Cursor plan file)

## Outcome
- The OM-I-3015 EasyPost tracker sync and delivery chain run on their own flag, `OM-I-3015-easypost-tracker-sync`.
- The WMS-I-1006 ship confirmation stays on `WMS-I-1006-roosevelt`. One toggle no longer controls two unrelated integrations.
- The flag ships disabled in prod. The OM-I-3015 chain pauses there until the flip ticket enables it.

## What shipped
- PR [#2821](https://github.com/WarbyParker/monocle_integrations/pull/2821) — the flag split (3 commits: flag + wiring, docs, review-triage fixes). Open, `enhancement` label applied.

## Decisions
### Functional clarifications (Q&A)
1. Flag values per environment → prod ships disabled; the other environments keep the old flag's values (Luis, chat, 2026-10-22).

### Design decisions (ours)
1. Move the whole chain to one flag: the tracker sync and the delivery chain together. The old flag mixed two unrelated integrations.
2. Keep the ship-confirm tracking-reference write on `WMS-I-1006-roosevelt`. Saving references at ship confirm is WMS-I-1006 behavior.
3. Rollout order: `OM-I-3015-easypost-tracker-sync`, then `IN-I-2017B-persist-tracking-references`, then `OM-I-3015-omg-returns`. Each flip is a full deploy, so dependents never outrun their prerequisites.
4. No DLQ redrive while the flag is false. Every DLQ arrival already opens a Jira ticket in the event handler, so nothing strands silently.
5. Review triage (9-seat panel, user verdicts): applied the docstring, test-rename, and `flags`-local idiom fixes. Skipped the half-flip guard (flags are per Lambda instance) and the dead `UpdateDeliveryDateStep.__call__` (belongs to that chain's author).

## Evidence
- 2026-10-22, local: full unit suite 7947 passed, coverage gate at 100.00% (host venv on the worktree).
- 2026-10-22, local dev container + LocalStack: scoped API/event suites 23 passed (enqueue API, process handler, fail handler).

## Test data
- Scoped suites: `monocle_integrations/_api/_test/_wp_om_i_3015_enqueue_tracking_references_api_test.py` and `monocle_integrations/_event_handlers/_test/_wp_om_i_3015_{process,fail}_tracking_reference_test.py`.

## Open items
- PR #2821 review and merge. Blocked on team review.
- The flip ticket owns the prod catch-up: re-enqueue the pause-window delivered rows from the carrier-events table.
- Before the prod apply: drain the tracker-sync queue. After the flip: reset ENQUEUED tracking references to PENDING.
- Pre-existing and unrelated: the TLS certifi emudhra-roots unit test fails on main (certifi bundle drift). Needs its own ticket.

## Artifacts
- PR: https://github.com/WarbyParker/monocle_integrations/pull/2821
- Review scratch: `monocle_integrations/tmp/om-i-3015_review/` (panels, triage verdicts, debate).
- Docs: `monocle_integrations/.docs/architecture/integrations.md` updated to the new flag.
