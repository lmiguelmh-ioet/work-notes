# OTCM-139192 — transaction_failures: read API
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-139192
- **RICE**: none — parent epic [OTCM-106900](https://warbyparker.atlassian.net/browse/OTCM-106900) (OIC Integration Error Handling)
- **Repos**: monocle_integrations
- **Status** (as of 2026-10-07): In flight — PRs 1, 2, 3a, 3b, 4, 5 of 9 open for review
- **Plan**: [otcm-139192_transaction_failures_read_api.plan.md](../monocle_integrations/.cursor/plans/otcm-139192_transaction_failures_read_api.plan.md) (lives in the monocle_integrations repo)

## Outcome
- The transaction_failures read API ships as a stacked 9-PR series on monocle-app.
- The auth groundwork, port contract, cursor codec, and both DynamoDB readers are open for review.
- Nothing is deployed. All merged code stays inert until the facade and route PRs land.

## What shipped
- [PR #2630](https://github.com/WarbyParker/monocle_integrations/pull/2630) — PR 1: auth whitelist path-template matching + presence-only Cloudflare JWT authenticator (inert groundwork). Open, base `main`. Self-review `7155976db`.
- [PR #2649](https://github.com/WarbyParker/monocle_integrations/pull/2649) — PR 2: port contract — reader ABCs, frozen Query/Record/Page models, disjoint exceptions. Open, base `main`. Hardening `eba49fc8a` after the 12-agent panel.
- [PR #2654](https://github.com/WarbyParker/monocle_integrations/pull/2654) — PR 3a: cursor encoder + filters hasher. Open, stacked on #2649.
- [PR #2652](https://github.com/WarbyParker/monocle_integrations/pull/2652) — PR 3b: cursor decoder (keeps the original codec PR's history). Open, stacked on #2654. Hardening `fdaa3da9d` after the 12-agent panel (18 findings).
- [PR #2653](https://github.com/WarbyParker/monocle_integrations/pull/2653) — PR 4: by-id DynamoDB reader, item mapper, adapter wiring. Open, stacked on #2652. Hardening `29ff3ef8e` after the 12-agent panel (20 findings, 12 applied).
- [PR #2659](https://github.com/WarbyParker/monocle_integrations/pull/2659) — PR 5: list DynamoDB reader with the GSI picker. Open, stacked on #2653. Hardening `765cc4ba1` after the 12-agent panel (23 findings, 1 BLOCKER: `rice_id` was dropped when `order_id` drove the index).

## Decisions

### Functional clarifications (Q&A)
1. Combined list params: the most specific param drives the index (`order_id` → `rice_id` → `status`); the rest filter afterward; pages may return fewer than `limit`; clients rely on `hasMore` (Luis, Jira comment 955841, 2026-10-05).
2. Invalid input returns 400 (Luis, same comment).
3. Pagination has no page numbers or totals (Luis, same comment).

### Design decisions (ours)
1. Ship as an 8-PR stacked series (contract → codec → readers → facade → routes → auth) to keep each PR reviewable.
2. The cursor carries the DynamoDB `LastEvaluatedKey` plus a SHA-256 filters fingerprint. Filter changes invalidate the cursor. `limit` is excluded so page size can change between pages.
3. The decoder reads valid key attributes from live table metadata (`from_table`). A new GSI needs no codec change.
4. The by-id reader returns `None` on a miss; the route PR maps it to 404.
5. The by-id record returns the full `invocations` history. The writer (OTCM-138120) owns growth and has no cap today. The list endpoint omits or truncates `invocations` in a later PR. Risk: past ~400 KB the item becomes unwritable.
6. Non-`ClientError` boto failures stay unwrapped, matching the writer and sibling adapters (PR4 panel question, kept).
7. `GetItem` stays eventually consistent (no `ConsistentRead`); acceptable for an ops UI (PR4 panel question, accepted).
8. One shared mock factory (`mock_transaction_failure_dynamodb_factory`) serves both transaction-failure adapter packages (PR4 panel finding, unified in PR4).
9. Filters that lose the index pick become `FilterExpression`s, including `rice_id` when `order_id` drives (ticket picker spec; PR5 panel BLOCKER, fixed before opening 2026-10-07).
10. The bare-listing `FAILED` default and the UTC ISO normalization are single-sourced in `_shared.py`, used by both the list reader and the cursor hasher (PR5 panel, applied 2026-10-07).
11. The cursor decoder wires statically from `_constants.KEY_ATTRIBUTES`; no live schema read at wiring or first use. Supersedes the wiring half of decision 3; `from_table` stays available (Luis, PR5 panel, 2026-10-07).
12. Every DynamoDB `ClientError` raises `TransactionFailureReaderError`; no start-key → 400 translation. Substring-matching an AWS-owned error message was too fragile to own (Luis, PR5 panel, 2026-10-07).

## Evidence
- No QA runs yet; all code is inert. Unit gates before each push: PR2 6599 tests, PR3 6633, PR4 6662, PR5 6693 — 100% coverage each time.

## Test data
- None yet. Unit fixtures only (`_adapters/_transaction_failure_readers/_fixtures.py`).

## Open items
- PRs 6–8: facade wiring, API routes with the CF-JWT guard, localstack API tests.
- PR 7 validates `limit` as `ge=1, le=100`; a sub-1 limit otherwise escapes as a raw botocore `ParamValidationError` (PR5 panel catch, recorded in the plan).
- AVP enforcement is blocked on OTCM-139191; API logic proceeds in shadow mode.
- Clean up the dead `_aws_dynamodb_transaction_failures_client` wiring in the facade PR (PR4 panel note).
- Localstack writer→reader round-trip test deferred to the route PR (API-level 200/404 coverage).

## Artifacts
- Spec: the ticket description is the spec; no FSD exists.
- Day notes: [day-20261006](day/day-20261006.md), [day-20261007](day/day-20261007.md).
- Skills touched: `self-review` (created), `pr-review` (pre-opening panels).
