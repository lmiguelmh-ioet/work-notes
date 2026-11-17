# OTCM-138123 — WMS-I-1005: pick-confirmation idempotency + transaction_failures replay
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-138123
- **RICE**: WMS-I-1005
- **Repos**: monocle_integrations
- **Status** (as of 2026-11-17): DONE — QA moved the ticket 2026-11-17 09:55 EST; this file is FROZEN. PRs #2900 + #2904 merged 2026-11-17; stage Run Evidence comment 986809. Residuals: follow-up drafts (replay lifecycle, one-table store, TO line-level matching, Boundary 2 ESS-cancel, OMG dedupe) stay unfiled — named owners in Open items.
- **Plan**: [projects.WMS-I-1005.OTCM-138123.plan.md](projects.WMS-I-1005.OTCM-138123.plan.md) — frozen verbatim archive at close 2026-11-17 (main plan `monocle_integrations/.cursor/plans/otcm-138123_idempotency_+_replay_8462d0b0.plan.md` + stage-QA run plan `~/.cursor/plans/otcm-138123_stage_qa_runs_460d1d98.plan.md`)

## Outcome
- PR1 + PR2 MERGED 2026-11-17 after stage QA evidence cleared both merge gates (Jira comment 986809: 14 of 15 scenarios pass; S9 discloses an ESS-cancel redelivery boundary with a follow-up drafted).
- The 2-PR stack implements the spike's two idempotency changes (re-scoped from 6 PRs on 2026-11-11: the replay machinery moved to unfiled follow-up drafts in `notes/future-work/`).
- PR1: the pick confirmation skips an order when every request-matched shipment line is pick-terminal, instead of failing the run on WMS retries.
- PR2: the pick confirmation counts work an earlier attempt already confirmed and caps each slip line by the open picked budget, so a replay confirms only the open work.

## What shipped
- [monocle_integrations #2900](https://github.com/WarbyParker/monocle_integrations/pull/2900) — PR1: pick-terminal set + request-matched classifier + skip-success on pick-terminal duplicates + skip-aware OMG publish exclusion. **MERGED 2026-11-17** (`enhancement`). Reworked 2026-11-11 to FSD §10 compliance (decision 12): unmatched request keys fail (`PickConfirmNoMatchingShipmentLinesError`), fully canceled orders fail and any ship-confirmed matched line fails (`PickConfirmNotAllowedError`) — skip-success covers only Staged/Interfaced/`Pending inventory processing` duplicates, which have no FSD error row. Reworked again 2026-11-12 (rounds 4–5, tips `2e16822b2` + `7b7c10cf5`): the status-name split is gone — all four post-ship statuses share the quantity gate (decision 13); null/missing `PickedQuantity` reads as 0. All 13 review threads answered. **Approved 2026-11-13** (Guillermo, Johnny Coral). Merge gate: (a) stage evidence that `Pending inventory processing` is pick-terminal, (b) stage evidence that Oracle safely rejects a double-confirm POST.
- [monocle_integrations #2904](https://github.com/WarbyParker/monocle_integrations/pull/2904) — PR2: done-work quantity counting + picked-budget slip allocation + per-line Short Pick reason + hardening refusals. **MERGED 2026-11-17** (`enhancement`); was stacked on #2900 (stack #2905). Three light panel rounds resolved. Rebased 2026-11-13 onto PR1's `7b7c10cf5` (force-pushed, tips `1aae10dcd` + `f0e863ee0`): the `counted`/`done` partition moved into the classifier, so the budget math inherits the quantity gate (decision 14). Gates green on the rebased branch: 363 scoped + 13 API + 9,623 unit at 100% coverage, mypy strict.

## Decisions
### Functional clarifications (Q&A)
1. Scope = implement spike changes #1/#2 AND design the replay mechanism (owner, plan Q1, 2026-11-10).
2. Adopt the wider pick-terminal set including `Pending inventory processing`; the mandate is ZERO side effects on retry (owner, plan Q2, 2026-11-10).
3. Request-matched scoping everywhere: SO by FR id, TO by item (owner, plan Q3, 2026-11-10). Whole-order scoping would post sibling slip lines as short picks.
4. ~~All-canceled pick conf skips successfully~~ — SUPERSEDED 2026-11-11 by decision 12: the FSD scenario demands failure + Jira ticket, so the code complies (owner: "we should do what the FSD says").
5. Short Pick reason belongs only on actual quantity mismatch (Alexis Tomacruz, FSD comment 2026-05-28). Drives PR2's per-line reason rule, QA sign-off AC4-e.
6. ~~Partially covered pick confirmations are not real traffic ("cuando nos paso?"), but at least a WARNING is wanted (Gabriel, Slack, 2026-11-10)~~ — SUPERSEDED 2026-11-11 by decision 12: partial coverage now fails with a ticket (FSD §10 "order or line does not exist"), which is louder than the WARNING Gabriel asked for.

### Design decisions (ours)
1. Skip representation: `ERPPickedDetail` with no lines + additive `skip_reason`; never leaks into SO event payloads (events build from `PickOrder`).
2. Publish exclusion by object identity, not by the lossy (org, ship_set, order_number) key; a key collision logs a WARNING with the colliding work units (PR1 review round 1, 2026-11-10).
3. Overpick/quantity-mapping failures keep the new `validate_shipment_lines` failed_step bucket; the shift is named in the PR description for OEH reporting instead of restoring the old bucket (PR1 review round 1, 2026-11-10).
4. The skip log stays a plain interpolated message because QA greps that text for AC4-d evidence; no structured field (PR1 review round 1, 2026-11-10).
5. Publish-loss window on the skip path is accepted until PR4a: comments name the manual-republish path now, and PR4a designs the DynamoDB publish ledger (PR1 review round 1, 2026-11-10).
6. No pick-evidence guard on the skip predicate in PR1: `picked_quantity` population is unvalidated on live data, and a naive guard breaks the mandated retry skip (PR1 review round 1, 2026-11-10). Stage check rides AC4-f.
7. No-eligible error message lists unworkable lines keyed by line id — (line id, item, status, FR) for SOs — because (item, status) keying collapses multi-FR orders (PR1 review round 2, 2026-11-10).
8. Manual reprocessing is the last resort, never the standing recovery (owner, PR1 review discussion, 2026-11-10). Consequences: the PR4a replay gate republishes automatically when the replayed row's failed_step is `publish_fulfillment_pick_event`, and the publish ledger is committed PR4a scope (candidate to fold into PR3's Terraform to shrink the exposure window), no longer a decision point.
9. ~~Uniform warn-and-skip on partial coverage~~ — SUPERSEDED 2026-11-11 by decision 12.
10. Empty-confirm guard always raises `PickConfirmationError`, never skip-success — an empty mapped set stays the same loud failure as live (owner veto, 2026-11-10). PR4b's replay path classifies that error as already-done when the row's step is `create_pick_confirm`.
11. Null `RequestedQuantity` replicates live exactly (owner, 2026-11-10; supersedes the same-day "posts 0" veto — the panel proved "posts 0" was never the live behavior).
    - The item's only slip line absorbs the done-aware open budget, identical to live on a first attempt.
    - A multi-line item raises typed `PickConfirmAllocationError` instead of crashing `TypeError`.
    - Raw picked stays visible on a per-item adjust log line (owner directive: include the raw picked somewhere).
12. FSD §10 compliance over warn-and-skip (owner, 2026-11-11): any unmatched request key fails (`PickConfirmNoMatchingShipmentLinesError` — §10 "order or line does not exist"); a fully canceled order fails (`PickConfirmNotAllowedError` — §9 canceled-TO scenario, §10 "order or line canceled"); any request-matched ship-confirmed line fails (`PickConfirmNotAllowedError` — §10 "ship confirmed and not yet picked"). Skip-success keeps only the statuses with no FSD error row (Staged, Interfaced, `Pending inventory processing`) — the in-flight duplicate case that is the OEH noise. A canceled line mixed with pick-done lines still skips (only the fully canceled order fails). The §9/§10 FSD addendum request is cancelled: the code matches the FSD. Two code comments cite the FSD requirement (owner-approved exception to the no-FSD-citation rule). The status-name split within the post-ship set is SUPERSEDED 2026-11-12 by decision 13; the §10 failure contract itself (unmatched keys, all-canceled, ship-confirmed-unpicked) stands.
13. Quantity gate replaces the status split for post-ship lines (owner, 2026-11-12, PR1 review round 4): Staged stays an unconditional skip; the four post-ship statuses share one rule — `picked_quantity > 0` → pick-done (skip), `== 0` → refuse ship-confirmed-and-not-yet-picked. Driver: Guillermo's IN-I-2017B lifecycle evidence — Oracle moves lines Shipped → `Pending inventory processing` → Interfaced 7–28s after ship confirm, so the split ticketed a redelivery at second 0 and skipped the identical one at second 30. The reader coerces null/missing `PickedQuantity` to 0 (guard survived the round-5 revert vote; a prod S3 sweep of 24k+ payloads found zero negative values).
14. The `counted`/`done` line partition lives in the classifier, not the processor (agent, PR2 rebase resolution 2026-11-13): `ShipmentLineClassification.counted_lines`/`done_lines`, with `done` = pick-terminal under the quantity gate, so PR2's done-work accounting follows the same semantics as the skip. Pending the parallel tab's veto.

## Evidence
- 2026-11-16 22:00–23:08 UTC, stage Lambda (vstage458, tip `8555b8064`) → evdi-test. 15 scenarios: 14 pass; S9 discloses a boundary (an ESS-cancel redelivery posts the remainder — production's own path does this too; follow-up drafted).
- Jira Run Evidence comment 986809 (posted 2026-11-17) with 6 attachments: full CloudWatch pull, ESS submit artifacts, before/after diffs, OEH watch, 13-payload zip + manifest, follow-up draft.
- A four-seat audit panel re-verified the draft before posting: 26/26 live-reproducible claims pass; two wording errors fixed (Boundary 1 subtraction ordering, ESS artifact timestamps).

## Test data
- Unit fixtures: `monocle_integrations/_domain/_integrations/_wp_wms_i_1005_wms_to_oracle_pick_confirmation/_fixtures.py`. No stage orders yet.

## Open items
- ~~QA sign-off on the stage evidence (AC4-b/d/e behavior changes)~~ — RESOLVED 2026-11-17: QA moved the ticket to Done on the stage evidence (comment 986809).
- Jira items parked in `tmp/otcm138123_jira_drafts.md` for the user to post: the comment-983437 amendment (quantity gate), the R4.16 partial-pick boundary question, the follow-up Task draft.
- Boundary 2 follow-up (ESS-cancel redelivery posts the remainder): draft attached to evidence comment 986809 (`monocle_integrations/tmp/otcm138123_followup_ess_cancel_draft.md`) for the functional/Oracle owner to file — the agent never files tickets.
- Functional question: does Manhattan ever redeliver a pick confirmation with altered quantities? If yes, the accounting design belongs to PR2 (merged; answer now informs a hardening follow-up).
- Functional/OIC-owner confirmation: no parallel pick-confirm writer exists for OMG-sourced SOs. A parallel writer would upgrade the deferred publish-ledger design from option to mandatory.
- Replay machinery (former PR3/PR4a/PR4b/PR4c): moved out of scope 2026-11-11 (owner + lead decisions) to unfiled drafts in `notes/future-work/` (`followup_transaction_failures_replay_lifecycle.md`, `one_table_state_store_baseline.md`).
- Follow-up ticket draft (file only, never filed): TO line-level matching, `tickets/OTCM-138123/followup_to_line_level_matching.md`.

## Artifacts
- Run evidence package: Jira comment 986809 attachments (raw CloudWatch pull of 4,334 events, ESS submit artifacts, duplicate-skip diffs, OEH watch JSON, 13-payload zip + manifest, ESS-cancel follow-up draft). Working scratch `/tmp/otcm138123_evidence/` is ephemeral.
- Spike: [WMS-I-1005 Pick Confirm Auto-retry and idempotency](https://warbyparker.atlassian.net/wiki/spaces/OT/pages/10536812552) (Johnny Coral, v13, 2026-10-05). Recs #3/#6 already done; #1/#2 = this stack; #5 = the replay design.
- FSD synced 2026-11-10 (v1.8, 2026-07-14, predates roosevelt) into the `integrations` repo, unstaged — user decides on commit.
- PR1 review records: `monocle_integrations/tmp/otcm138123_pr1_review/triage_plan.yaml` (16 findings, round 1) and `monocle_integrations/tmp/otcm138123_pr1_review_r2/triage_plan.yaml` (12 findings, round 2) — all resolved, all fixes applied.
- PR2 review records: `monocle_integrations/tmp/otcm138123_pr2_review/triage_plan.yaml` (round 1, 21 findings). Rounds 2–3 ran as ephemeral panel scratch (findings applied, not archived).
