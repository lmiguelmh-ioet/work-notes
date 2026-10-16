# OTCM-146798 — RMCS-I-3001: CPU pickup-task PoD, QC-fail replacement chain, warranty returns

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-146798
- **RICE**: RMCS-I-3001 (follow-on of OTCM-139313 / PR #1105)
- **Repos**: oracle-integration-cloud (DM only)
- **Status** (as of 2026-10-16): all 5 work items written + validated; review round 1 fixed + verified; dev1 catalog upload pending authorization
- **Plan**: `monocle_integrations/.cursor/plans/rmcs-i-3001_cpu_qcfail_warranty_returns.plan.md`

## Outcome

- In flight — the PoD data model now sources CPU orders from the pickup-task completion, redirects QC-failed lines to their replacement's pickup, and handles warranty returns (partial refund moves the .3 PoD + end date to the credit-memo date; full refund suppresses every pending PoD and U).
- A 12-reviewer pre-opening panel found 4 real blockers (all in the new limbs); all fixed and re-verified byte-identical on dev1.

## What shipped

- Nothing merged yet. Work product: branch `OTCM-146798-rmcs-i-3001-pod-dm` (worktree `oracle-integration-cloud/tmp/otcm146798-wt`), DM +292/−43 vs the OTCM-139313 baseline, then review-fix delta on top; nothing committed as of 2026-10-16.

## Decisions

### Functional clarifications (Q&A)

1. Full-refund suppression scope — suppress every pending PoD for the warranty line, no .2 and no .3, forever (Aruna, FSD comment 2026-10-15); the .1 is never pending at return time, so the code suppressing it too matches FSD "No additional POD load is needed".
2. Partial refund — set SRC_ATTRIBUTE_DATE1 to the return (credit memo) date and load the .3 PoD at that same date in the same upload (Luis proposal, FSD comment 2026-10-16 thread).
3. Warranty EFF attribute_char2 cross-order branch — struck from the FSD (line 421), so the DM dropped it (FSD edit, synced 2026-10-16).
4. Covered-line EFF carries the order line NUMBER, not the internal id (Aruna/Ranjeeth, FSD comments 2026-10-03, item 2.1) — for the Warranty EFF; the QC replacement EFF char5 semantics stay a merge gate (Q1).

### Design decisions (ours)

1. Return detection = 3003's merged gate: `WP_WARRANTY_RETURN` line + completed OMG CM via `ct_reference` = return order number, linked per return line through `doo_document_references` (`ddr.line_id = l.line_id`) — header-grain aggregation cross-contaminated refunds (review blocker R1-03).
2. `warranty_line_state` reads the latest non-terminal .3 interface row: U writes land as NEW rows, the original row never carries them; EFF dedup compares live state vs computed (TRUNC both sides — time components churned).
3. Interface dedup blocks only in-flight rows (`NOT_PROCESSED`/`UPDATE_NOT_PROCESSED`): processed rows must not block the return re-emit; dev1 vocabulary = PROCESSED/UPDATE_PROCESSED/REJECTED/UPDATE_REJECTED.
4. Version-row pin: earliest VIABLE interface row per split line (anti-join on creation_date) — probe proved `version_flag`/`version_number` never discriminate (all 'N'/1); U-written rows fanned out the base join (review blocker R1-02).
5. char5 conversion is fail-loud on purpose (user decision 2026-10-16): a junk value fails the run until the bad EFF data is fixed; ROW_NUMBER partitions by the converted value ('03' vs '3' duplicate-rank fix).
6. Late-return gate: a return at/after the computed end date moves nothing (FSD scopes the move to returns before expiry); functional confirmation pending (Q4).
7. `rmcs_lines_base` → `rmcs_lines` split: the fulfillment-date CASE existed 4× (unanimous panel finding); now computed once, emission gates outside.

## Evidence

- QA-17 full-extract A/B (2026-10-16, dev1, window 6/01–10/16): 10 rows identical to the 681-line baseline, 3 explained new rows (TNAQ4YG02Z CPU backlog drain at go-live).
- Post-review A/B (2026-10-16, dev1): pre-fix vs post-fix, 6 pairs byte-identical (9-row wide window, order-numbers 274/277/281/310, FIN-008 compile).
- Review panel run 20261016T1024: 12/12 seats, consolidated at `oracle-integration-cloud/tmp/otcm146798_review/consolidated.md`.
- Probes (dev1): version-row shapes (40 rows, VF='N'/VN=1), `doo_document_references.line_id` populated, zero OMG CMs on dev1 AND stage; prod arbiter report not permitted.

## Test data

- dev1 warranty orders 274/275/277/281/284/298/310/314 + POC*/RMA* series (interface rows incl. multi-version keys 277/281, rejected-then-reload 298, char2 order 310).
- CPU backlog order TNAQ4YG02Z (WP_B2C_CPU, pickup 2026-09-16, delivery NULL forever).
- Warranty-return path has NO test data anywhere (zero OMG CMs) — needs Guillermo's QA return orders with completed credit memos.

## Open items

- NEW 2026-10-16 PM: mapping re-grain (Aruna, Slack + mapping sheets + 2 assigned cell comments) — all RMCS components re-key source-doc ids to fulfillment/delivery grain. DM impact: two bind joins must go cutover-tolerant (`IN (line_id, fulfill_line_id)`); dev1 already has 2 fulfill-keyed interface rows. Open ambiguity: addl_sub_line key (delivery_detail_id vs combination). Analysis: `tmp/otcm146798_review/mapping_regrain_20261016.md`. Replies anchor at Aruna's comments VRM_SOURCE_DOC_LINES!D4 / VRM_SOURCE_DOC_ADDL_SUBLINES!D21.

- dev1 catalog upload (authorized text + live verify), then user re-exports `.xdm.catalog`, commit, PR.
- Merge gates after triage (`questions_to_route.md`, 3-agent panel 2026-10-16, exact ask-locations per question): Q1 char5 line-id vs line-number (FSD Scenario 4 points at internal id, opposite the current join; dev1 probes 2026-10-16 not decisive — char5 NULL on real orders, only orphan TST rows carry '1'; bumped the existing FSD thread to Ranjeeth), Q2 ct_reference format on prod OMG CMs (new FSD comment on the Warranty Return Flow section), Q3 prod char2 count (data request in Bhanu's SQL thread — exact query attached; we lack prod access).
- Already routed: covered-item QC-fail (Q7) sits unanswered in the FSD thread since 2026-10-16 — chase, non-blocking.
- Triage dropped Q4/Q5/Q6/Q8/Q9/Q10/Q11 with documented assumptions (`triage/consolidated_triage.md`); Q10's lifecycle gets an empirical probe on the first closed CPU order before prod.
- Return-path end-to-end proof blocked on Guillermo's warranty-return QA data.
- Prod gates: task setup confirmation, explain plans on stage (unwindowed CTEs).

## Artifacts

- FSD + comments: `integrations/RMCS-I-3001/docs/drive/RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.md`
- Review pack: `oracle-integration-cloud/tmp/otcm146798_review/` (diff, briefs, round1 reports, consolidated, questions_to_route)
- A/B harness artifacts: `monocle_integrations/tmp/dm_rev_*`, snapshots `dm_item0..5_state.sql`, `dm_prereview_state.sql`
- Skills: fusion-sql (RP_ARB usage), bip-catalog-sync (upload pending)
