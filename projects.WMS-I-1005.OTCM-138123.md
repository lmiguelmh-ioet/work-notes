# OTCM-138123 — WMS-I-1005: pick-confirmation idempotency + transaction_failures replay
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-138123
- **RICE**: WMS-I-1005
- **Repos**: monocle_integrations
- **Status** (as of 2026-11-10): In flight — PR1+PR2 of 6 open (stack #2905), awaiting review + stage-evidence merge gate
- **Plan**: [projects.WMS-I-1005.OTCM-138123.plan.md](projects.WMS-I-1005.OTCM-138123.plan.md) (archive, snapshot at PR1 opening) · live copy: `monocle_integrations/.cursor/plans/otcm-138123_idempotency_+_replay_8462d0b0.plan.md` (gitignored, evolves with the stack)

## Outcome
- In flight. The 6-PR stack implements the spike's two idempotency changes plus an operator-triggered replay endpoint for WMS-I-1005 `transaction_failures` rows.
- PR1 opened 2026-11-10: the pick confirmation skips an order when every request-matched shipment line is pick-terminal, instead of failing the run on WMS retries.
- PR2 opened 2026-11-10: the pick confirmation counts work an earlier attempt already confirmed and caps each slip line by the open picked budget, so a replay confirms only the open work.

## What shipped
- [monocle_integrations #2900](https://github.com/WarbyParker/monocle_integrations/pull/2900) — PR1: pick-terminal set + request-matched classifier + skip-success + warn-and-skip on unmatched/ineligible lines + skip-aware OMG publish exclusion. Open, `enhancement`. Reworked 2026-11-10 after Gabriel's answer (clarification 6): the two strict raises became WARNING + order skip (both order types, decision 9); pushed as `314946aa0`, PR body updated. Merge gate: (a) stage evidence that `Pending inventory processing` is pick-terminal, (b) stage evidence that Oracle safely rejects a double-confirm POST.
- [monocle_integrations #2904](https://github.com/WarbyParker/monocle_integrations/pull/2904) — PR2: done-work quantity counting + picked-budget slip allocation + per-line Short Pick reason + hardening refusals. Open, `enhancement`, stacked on #2900 (stack #2905). Three light panel rounds resolved; full-repo coverage gate green (8,868 passed, 100%).

## Decisions
### Functional clarifications (Q&A)
1. Scope = implement spike changes #1/#2 AND design the replay mechanism (owner, plan Q1, 2026-11-10).
2. Adopt the wider pick-terminal set including `Pending inventory processing`; the mandate is ZERO side effects on retry (owner, plan Q2, 2026-11-10).
3. Request-matched scoping everywhere: SO by FR id, TO by item (owner, plan Q3, 2026-11-10). Whole-order scoping would post sibling slip lines as short picks.
4. All-canceled pick conf skips successfully — overrides the FSD test scenario that demands failure + Jira ticket, because that ticket class is the OEH noise (owner, plan QA log AC4-d, 2026-11-10). Compensated by the `skip_reason` log.
5. Short Pick reason belongs only on actual quantity mismatch (Alexis Tomacruz, FSD comment 2026-05-28). Drives PR2's per-line reason rule, QA sign-off AC4-e.
6. Partially covered pick confirmations are not real traffic ("cuando nos paso?"), but at least a WARNING is wanted (Gabriel, Slack, 2026-11-10). Consequence: no error ticket and no zero-quantity exemption; PR1 warns and skips the order on any unmatched item/FR, both order types.

### Design decisions (ours)
1. Skip representation: `ERPPickedDetail` with no lines + additive `skip_reason`; never leaks into SO event payloads (events build from `PickOrder`).
2. Publish exclusion by object identity, not by the lossy (org, ship_set, order_number) key; a key collision logs a WARNING with the colliding work units (PR1 review round 1, 2026-11-10).
3. Overpick/quantity-mapping failures keep the new `validate_shipment_lines` failed_step bucket; the shift is named in the PR description for OEH reporting instead of restoring the old bucket (PR1 review round 1, 2026-11-10).
4. The skip log stays a plain interpolated message because QA greps that text for AC4-d evidence; no structured field (PR1 review round 1, 2026-11-10).
5. Publish-loss window on the skip path is accepted until PR4a: comments name the manual-republish path now, and PR4a designs the DynamoDB publish ledger (PR1 review round 1, 2026-11-10).
6. No pick-evidence guard on the skip predicate in PR1: `picked_quantity` population is unvalidated on live data, and a naive guard breaks the mandated retry skip (PR1 review round 1, 2026-11-10). Stage check rides AC4-f.
7. No-eligible error message lists unworkable lines keyed by line id — (line id, item, status, FR) for SOs — because (item, status) keying collapses multi-FR orders (PR1 review round 2, 2026-11-10).
8. Manual reprocessing is the last resort, never the standing recovery (owner, PR1 review discussion, 2026-11-10). Consequences: the PR4a replay gate republishes automatically when the replayed row's failed_step is `publish_fulfillment_pick_event`, and the publish ledger is committed PR4a scope (candidate to fold into PR3's Terraform to shrink the exposure window), no longer a decision point.
9. Uniform warn-and-skip on partial coverage: any unmatched request item (TO) or FR (SO) skips the whole order with a WARNING naming the unmatched keys — no scoped proceed, matching the pre-rework strict-fail shape without the ticket (owner directive, 2026-11-10; supersedes the short-lived TO-proceeds/SO-skips asymmetry considered earlier the same day).
10. Empty-confirm guard always raises `PickConfirmationError`, never skip-success — an empty mapped set stays the same loud failure as live (owner veto, 2026-11-10). PR4b's replay path classifies that error as already-done when the row's step is `create_pick_confirm`.
11. Null `RequestedQuantity` replicates live exactly (owner, 2026-11-10; supersedes the same-day "posts 0" veto — the panel proved "posts 0" was never the live behavior).
    - The item's only slip line absorbs the done-aware open budget, identical to live on a first attempt.
    - A multi-line item raises typed `PickConfirmAllocationError` instead of crashing `TypeError`.
    - Raw picked stays visible on a per-item adjust log line (owner directive: include the raw picked somewhere).

## Evidence
- Pending. The QA matrix runs on stage after PR1/PR2 land; per-scenario evidence follows the `jira-qa-evidence` standard.

## Test data
- Unit fixtures: `monocle_integrations/_domain/_integrations/_wp_wms_i_1005_wms_to_oracle_pick_confirmation/_fixtures.py`. No stage orders yet.

## Open items
- Stage validation before PR1 merge: `Pending inventory processing` pick-terminal assumption; Oracle double-confirm POST behavior; `picked_quantity` population (AC4-f).
- FSD §9/§10 addendum request so the contract of record matches the shipped skip-success behavior. Follows PR1 merge; rides the QA task.
- Functional question: does Manhattan ever redeliver a pick confirmation with altered quantities? If yes, the accounting design belongs to PR2.
- Functional/OIC-owner confirmation: no parallel pick-confirm writer exists for OMG-sourced SOs. A parallel writer upgrades PR4a's publish ledger from option to mandatory.
- PR3–PR4c per the plan. PR4c blocked on the OTCM-139192 read-API stack merging to main.
- Follow-up ticket draft (file only, never filed): TO line-level matching, `tickets/OTCM-138123/followup_to_line_level_matching.md`.

## Artifacts
- Spike: [WMS-I-1005 Pick Confirm Auto-retry and idempotency](https://warbyparker.atlassian.net/wiki/spaces/OT/pages/10536812552) (Johnny Coral, v13, 2026-10-05). Recs #3/#6 already done; #1/#2 = this stack; #5 = the replay design.
- FSD synced 2026-11-10 (v1.8, 2026-07-14, predates roosevelt) into the `integrations` repo, unstaged — user decides on commit.
- PR1 review records: `monocle_integrations/tmp/otcm138123_pr1_review/triage_plan.yaml` (16 findings, round 1) and `monocle_integrations/tmp/otcm138123_pr1_review_r2/triage_plan.yaml` (12 findings, round 2) — all resolved, all fixes applied.
- PR2 review records: `monocle_integrations/tmp/otcm138123_pr2_review/triage_plan.yaml` (round 1, 21 findings). Rounds 2–3 ran as ephemeral panel scratch (findings applied, not archived).
