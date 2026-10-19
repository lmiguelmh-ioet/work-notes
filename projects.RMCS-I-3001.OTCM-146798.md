# OTCM-146798 — RMCS-I-3001: CPU pickup-task PoD, QC-fail replacement chain, warranty returns

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-146798
- **RICE**: RMCS-I-3001 (follow-on of OTCM-139313 / PR #1105)
- **Repos**: oracle-integration-cloud (DM only)
- **Status** (as of 2026-10-19): all 7 work items written + validated on dev1; all Q&A resolved or dispositioned; dev1 catalog upload next, then live verify, user re-export, commit, PR
- **Plan**: `monocle_integrations/.cursor/plans/rmcs-i-3001_cpu_qcfail_warranty_returns.plan.md`

## Outcome

- In flight — the PoD data model now sources CPU orders from the pickup-task completion, redirects QC-failed lines to their replacement's pickup, and handles warranty returns (partial refund moves the .3 PoD + end date to the credit-memo date; full refund suppresses every pending PoD and U).
- A 12-reviewer pre-opening panel found 4 real blockers (all in the new limbs); all fixed and re-verified byte-identical on dev1.

## What shipped

- Nothing merged yet. Work product: branch `OTCM-146798-rmcs-i-3001-pod-dm` (worktree `oracle-integration-cloud/tmp/otcm146798-wt`), DM +394/−69 vs the OTCM-139313 baseline (items 1–7, uncommitted as of 2026-10-19). Item 7 (warranty-branch QC-fail redirect, from Q9's answer) landed 2026-10-19.

## Decisions

### Functional clarifications (Q&A)

1. Full-refund suppression scope — suppress every pending PoD for the warranty line, no .2 and no .3, forever (Aruna, FSD comment 2026-10-15); the .1 is never pending at return time, so the code suppressing it too matches FSD "No additional POD load is needed".
2. Partial refund — set SRC_ATTRIBUTE_DATE1 to the return (credit memo) date and load the .3 PoD at that same date in the same upload (Luis proposal, FSD comment 2026-10-16 thread).
3. Warranty EFF attribute_char2 cross-order branch — struck from the FSD (line 421), so the DM dropped it (FSD edit, synced 2026-10-16).
4. Covered-line EFF carries the order line NUMBER, not the internal id (Aruna/Ranjeeth, FSD comments 2026-10-03, item 2.1) — for the Warranty EFF; the QC replacement EFF char5 semantics stay a merge gate (Q1).
5. char5 of the replacement EFF carries the internal DOO line id, not the line number (Ranjeeth, FSD reply 2026-10-19); the DM join switched line_number → line_id. Inert on dev1 until real OMG replacement data.
6. ct_reference on OMG credit memos is always the Oracle return order number (Aruna, FSD reply 2026-10-19) — the warranty-return detection join is confirmed as built.
7. A warranty on a QC-failed covered line stays on the original order; no new warranty line is created on the replacement (Aruna, FSD reply 2026-10-19) — the .2/.3 dates follow the covered item's redirect (work item 7).
8. Sequential partial refunds on one covered item take the auto-reversal path (Aruna, FSD reply 2026-10-19) — confirms the built per-credit-memo handling.
9. QC fail applies only to CPU orders (Aruna, FSD reply 2026-10-19) — confirms the PICKUP_TASK-only redirect gating.
10. The pickup task-type-code ask was withdrawn (user decision 2026-10-19): the 'Pending Customer Pick Up' step-name filter is final, tacitly accepted by OM.

### Design decisions (ours)

1. Return detection = 3003's merged gate: `WP_WARRANTY_RETURN` line + completed OMG CM via `ct_reference` = return order number, linked per return line through `doo_document_references` (`ddr.line_id = l.line_id`) — header-grain aggregation cross-contaminated refunds (review blocker R1-03).
2. `warranty_line_state` reads the latest non-terminal .3 interface row: U writes land as NEW rows, the original row never carries them; EFF dedup compares live state vs computed (TRUNC both sides — time components churned).
3. Interface dedup blocks only in-flight rows (`NOT_PROCESSED`/`UPDATE_NOT_PROCESSED`): processed rows must not block the return re-emit; dev1 vocabulary = PROCESSED/UPDATE_PROCESSED/REJECTED/UPDATE_REJECTED.
4. Version-row pin: earliest VIABLE interface row per split line (anti-join on creation_date) — probe proved `version_flag`/`version_number` never discriminate (all 'N'/1); U-written rows fanned out the base join (review blocker R1-02).
5. char5 conversion is fail-loud on purpose (user decision 2026-10-16): a junk value fails the run until the bad EFF data is fixed; ROW_NUMBER partitions by the converted value ('03' vs '3' duplicate-rank fix).
6. Late-return gate: a return at/after the computed end date moves nothing (FSD scopes the move to returns before expiry); functional confirmation pending (Q4).
7. `rmcs_lines_base` → `rmcs_lines` split: the fulfillment-date CASE existed 4× (unanimous panel finding); now computed once, emission gates outside.
8. Re-grain join shape (user standing decision 2026-10-19): both-grain `IN (l.line_id, fl.fulfill_line_id)` on both branches. RMCS-I-3001 never reached prod, so old-record concerns were discarded and the simpler symmetric join wins.
9. The warranty-branch redirect mirrors the standard branch (2026-10-19): PICKUP_TASK covered orders only, replace-not-fallback, no new last-update analog — the redirect date pulls the row through the main GREATEST window.

## Evidence

- QA-17 full-extract A/B (2026-10-16, dev1, window 6/01–10/16): 10 rows identical to the 681-line baseline, 3 explained new rows (TNAQ4YG02Z CPU backlog drain at go-live).
- Post-review A/B (2026-10-16, dev1): pre-fix vs post-fix, 6 pairs byte-identical (9-row wide window, order-numbers 274/277/281/310, FIN-008 compile).
- QA-19 re-grain A/B (2026-10-19, dev1): 336 resolves via FULFILL_LINE_ID with the delivered-dd key; TestOrder62 dual-key no fan-out; wide window 9/9 with 4 intended dd-key flips. char5 fix A/B: 9/9 byte-identical.
- Item-7 warranty-redirect A/B (2026-10-19, dev1): wide window 9/9 byte-identical vs the pre-item-7 baseline; 348/353 order-numbers 0 rows both (held, pickups NOT_STARTED).
- Review panel run 20261016T1024: 12/12 seats, consolidated at `oracle-integration-cloud/tmp/otcm146798_review/consolidated.md`.
- Probes (dev1): version-row shapes (40 rows, VF='N'/VN=1), `doo_document_references.line_id` populated, zero OMG CMs on dev1 AND stage; prod arbiter report not permitted.

## Test data

- dev1 warranty orders 274/275/277/281/284/298/310/314 + POC*/RMA* series (interface rows incl. multi-version keys 277/281, rejected-then-reload 298, char2 order 310).
- CPU backlog order TNAQ4YG02Z (WP_B2C_CPU, pickup 2026-09-16, delivery NULL forever).
- Warranty-return path has NO test data anywhere (zero OMG CMs) — needs Guillermo's QA return orders with completed credit memos.
- 348/353 (Ranjeeth, 2026-10-19): the Q9 scenario pair. 348 is WP_B2C_CPU with QC-failed lines incl. covered line 1 (warranty on line 8); 353 replaces 348's line 1 (char6='348'). 353's char5 is mixed (internal id on some rows, '1' on others — flagged to Ranjeeth). All pickup tasks NOT_STARTED; QA-22 needs OM to complete 353's pickup.

## Open items

- ~~dev1 + stage catalog upload (authorized text + live verify)~~ — DONE 2026-10-19 16:40/16:47: CDATA-only swap (byte-proven) on both pods, round-trip sha256 match both, dev1 live report 9/9 = arbiter + 348/353 = 0 rows, stage 0 rows / 0 errors (execution proof). Next: user re-exports `.xdm.catalog` from dev1 → commit (approval) → PR — the immediate next step.
- Guillermo warranty-return QA data: fresh partials + one full-refund case with completed OMG credit memos. Blocks QA-11/12/14(full); newest dev1 CM is 2026-08-03.
- QA-22 live proof: OM (Ranjeeth) completes the pickup task on 353's replacement line; the 353 char5 mixed-semantics flag rides with that ask.
- Q18 probe: orchestration group stays ACTIVE on closed orders — empirical check rides with QA.
- Deploy order: 3003 (OTCM-146384, Guillermo, in Review) loads first, then 3001 PoD (confirmed by Aruna 2026-10-15).
- Prod gates: OM prod pickup-task setup timing; explain plans on stage (unwindowed CTEs).

## Artifacts

- FSD + comments: `integrations/RMCS-I-3001/docs/drive/RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.md`
- Review pack: `oracle-integration-cloud/tmp/otcm146798_review/` (diff, briefs, round1 reports, consolidated, questions_to_route)
- A/B harness artifacts: `monocle_integrations/tmp/dm_rev_*`, snapshots `dm_item0..5_state.sql`, `dm_prereview_state.sql`
- Skills: fusion-sql (RP_ARB usage), bip-catalog-sync (upload pending)
