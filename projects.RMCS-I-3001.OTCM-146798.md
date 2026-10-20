# OTCM-146798 — RMCS-I-3001: CPU pickup-task PoD, QC-fail replacement chain, warranty returns

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-146798
- **RICE**: RMCS-I-3001 (follow-on of OTCM-139313 / PR #1105)
- **Repos**: oracle-integration-cloud (DM only)
- **Status** (as of 2026-10-20): **PR #1141 OPEN** in oracle-integration-cloud, stacked on #1105 (commit `a53bfb96`, labeled enhancement). The round-3 DM is uploaded to dev1 + stage (round-trip sha256 `47b75f5a919b48ba` on each; dev1 live report = 9 rows) and the `.xdm.catalog` re-export matches the upload byte-for-byte; all six routed comments posted (Q22–Q27, answers pending). The PR merges at prod promotion, after RMCS-I-3003 (OTCM-146384)
- **Plan**: `monocle_integrations/.cursor/plans/rmcs-i-3001_cpu_qcfail_warranty_returns.plan.md`

## Outcome

- In flight — the PoD data model now sources CPU orders from the pickup-task completion, redirects QC-failed lines to their replacement's pickup, and handles warranty returns (partial refund moves the .3 PoD + end date to the credit-memo date; full refund suppresses every pending PoD and U).
- A 12-reviewer pre-opening panel found 4 real blockers (all in the new limbs); all fixed and re-verified byte-identical on dev1.

## What shipped

- **[PR #1141](https://github.com/WarbyParker/oracle-integration-cloud/pull/1141) OPEN 2026-10-20**, stacked on #1105: commit `a53bfb96`, DM `.sql` +535/−68 vs the OTCM-139313 baseline plus the re-exported `.xdm.catalog` (Bin 9,520 → 13,870 B, inflated SQL sha256 `47b75f5a919b48ba` == the pod upload). Labeled enhancement. Merges at prod promotion, after RMCS-I-3003 (OTCM-146384).
- Build-up: work items 1–7 (+394/−69) through 2026-10-19; round-2 fix batch +199/−64 (`tmp/otcm146798_impl/merged/base_to_merged.diff`); round-3 fix batch 11 change groups (canonical `tmp/otcm146798_r3_impl/merged/DM.sql` md5 `da46dc77…`, diff `merged/r2base_to_r3merged.diff`). All committed in `a53bfb96`.

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
11. Warranty price is always fixed, never discounted (Aruna, FSD reply 2026-10-20) — the full-refund classifier's qty × unit-price comparison is safe.
12. FSD §2.3 B2C CPU launch parameter updated by Aruna (2026-10-20): fetch CPU orders with delivery date updated; on CPU QC fail, the order-line EFF carries the original order number + line id — matches the built EFF resolution, no DM impact.

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
10. Round-2 gate layer (finding _19, user keep 2026-10-20): the late-return gate lives in its own CTE (`warranty_lines_gated`) with an explicit column list. The raw return date is not projected, so a missed consumer fails with ORA-00904 instead of reading the raw value.
11. Shared QC resolution (_09 option B, absorbing _06): one CTE (`qc_fail_resolution`) resolves a failed line's redirect, per-line reference first, order-level fallback. Both `rmcs_lines_base` and `covered_item_dates` consume it, and BOTH pickup fields (completion date and write date) follow the redirect.
12. WSH bridge grain (_04 + _13, probe-driven): delivery-source lines key by their own detail, tied by its assignment to the dated delivery (KEEP LAST). Fulfillment-source shipped lines key by their own detail through the new `shipped_line_details` CTE. The probe settled the scope question: wholesale lines do ship with WSH details (dev1 138/1,027, stage 11/39).
13. Warranty fulfill fan-out (_02): the both-grain key match is a semi-join (EXISTS), so several non-shippable fulfill rows per warranty line cannot duplicate PoD rows.
14. Standard-branch reload pin (_01): the earliest-viable pin mirrors the warranty branch (status filter + NOT EXISTS on creation_date).
15. `shipped_line_details` window (round-3 _03, user keep 2026-10-20): the CTE mirrors `fulfill_delivery`'s dual-mode predicate on `fl.fulfillment_date` — it no longer scans full shippable history every run. Verified output-inert statically (the standard branch emits only in-window/order-named FULFILLMENT rows) and by the byte-identical A/B.
16. `qc_fail_resolution` LEFT JOINs (round-3 _06 option A): a QC-failed line whose header exists only as a DOO_REFERENCE import stub now survives with NULL resolution dates, so the redirect arm HOLDS the line instead of silently emitting at its own pickup. Fail-held beats fail-silent-wrong; recoverable via order-numbers run after a data fix. Byte-identical on healthy data.
17. Best-of-3 implementation pattern with differentiated angles (surgical / stylist / skeptic), used for both merge rounds: the code hunks converged byte-identical across seats; the seats diverged only on comment wording, and the skeptic's anchor re-verification caught two geometrically infeasible "fits in 2 lines" register claims before they reached the file.

## Evidence

- QA-17 full-extract A/B (2026-10-16, dev1, window 6/01–10/16): 10 rows identical to the 681-line baseline, 3 explained new rows (TNAQ4YG02Z CPU backlog drain at go-live).
- Post-review A/B (2026-10-16, dev1): pre-fix vs post-fix, 6 pairs byte-identical (9-row wide window, order-numbers 274/277/281/310, FIN-008 compile).
- QA-19 re-grain A/B (2026-10-19, dev1): 336 resolves via FULFILL_LINE_ID with the delivered-dd key; TestOrder62 dual-key no fan-out; wide window 9/9 with 4 intended dd-key flips. char5 fix A/B: 9/9 byte-identical.
- Item-7 warranty-redirect A/B (2026-10-19, dev1): wide window 9/9 byte-identical vs the pre-item-7 baseline; 348/353 order-numbers 0 rows both (held, pickups NOT_STARTED).
- Review panel run 20261016T1024: 12/12 seats, consolidated at `oracle-integration-cloud/tmp/otcm146798_review/consolidated.md`.
- Round-2 panel run 20261020T0644: 12/12 seats, 19 deduped findings, register at `oracle-integration-cloud/tmp/otcm146798_review/panels2/all_findings.md`. User keep/drop executed; the round's blocker (_19 dead gate) verified by grep before fixing.
- Round-2 merged A/B (2026-10-20, dev1): '348'/'353' empty old and new; QA window 9/9 byte-identical (QA-19 keys hold); wide window 13/13 with one verified flip (order 248 line 300000896504426 → its own detail 4349296, fix _13). Stage: old/new empty in both windows and both order modes.
- Best-of-3 merge (2026-10-20): three independent implementations compared (`tmp/otcm146798_impl/a_vs_mine.diff`, `b_vs_mine.diff`); B's DM adopted plus the restored shippable filter and comment trims (9 hunks, `merged/b_to_merged.diff`). The base→merged diff was verified hunk-by-hunk against the approved findings.
- Round-3 panel run 20261020T0823: 12/12 seats, zero blockers, 15 findings (`tmp/otcm146798_review/panels3/all_findings.md`). User keep/drop 2026-10-20: apply 3/11/12/6A/9A/13/10/1/2/7/8/4; ignore 5 (DUMP probe disproved the bridge char-conversion premise), 14 (already resolved), 15 (record-only).
- Round-3 merged A/B (2026-10-20, dev1, harness `monocle_integrations/tmp/build_round3_ab.py`): QA window 9/9 md5-identical (`94bdb9c9…`), wide 13/13 md5-identical (`c3348e95…`), 348/353 empty on both variants; stage empty in both windows and both order modes on both variants. Round-3 regression gate PASSED.
- Pre-posting comment fact-check (2026-10-20, 3 independent seats, `tmp/otcm146798_impl/comment_check_{1,2,3}.md`): _15/_17/_16a/_16b POST AS-IS; _14 trimmed (the classifier was already confirmed at Q7); _18 reworded (no "Key Logic thread" exists — the pickup confirmation lives in the Q1 thread on the §1.1 "For CPU Orders" sentence).
- Round-3 catalog verification (2026-10-20): `updateObject` true on both pods; round-trip SQL == `merged/DM.sql` byte-for-byte on dev1 AND stage (sha256 `47b75f5a919b48ba`); dev1 live report through the deployed DM = 9 rows (= A/B QA baseline); the re-exported `.xdm.catalog` inflates to the same sha256.
- Probes (dev1): version-row shapes (40 rows, VF='N'/VN=1), `doo_document_references.line_id` populated, zero OMG CMs on dev1 AND stage; prod arbiter report not permitted.

## Test data

- dev1 warranty orders 274/275/277/281/284/298/310/314 + POC*/RMA* series (interface rows incl. multi-version keys 277/281, rejected-then-reload 298, char2 order 310).
- CPU backlog order TNAQ4YG02Z (WP_B2C_CPU, pickup 2026-09-16, delivery NULL forever).
- Warranty-return path has NO test data anywhere (zero OMG CMs) — needs Guillermo's QA return orders with completed credit memos.
- 348/353 (Ranjeeth, 2026-10-19): the Q9 scenario pair. 348 is WP_B2C_CPU with QC-failed lines incl. covered line 1 (warranty on line 8); 353 replaces 348's line 1 (char6='348'). 353's char5 is mixed (internal id on some rows, '1' on others — flagged to Ranjeeth). All pickup tasks NOT_STARTED; QA-22 needs OM to complete 353's pickup.

## Open items

- ~~dev1 + stage catalog upload (authorized text + live verify)~~ — DONE 2026-10-19 16:40/16:47: CDATA-only swap (byte-proven) on both pods, round-trip sha256 match both, dev1 live report 9/9 = arbiter + 348/353 = 0 rows, stage 0 rows / 0 errors (execution proof). SUPERSEDED 2026-10-20: round-3 re-upload DONE 2026-10-20 (user-authorized): `updateObject` true on both pods (dev1 60,963 B, stage 60,966 B), round-trip SQL == round-3 `merged/DM.sql` byte-for-byte on BOTH pods (sql sha256 `47b75f5a919b48ba`), dev1 live report through the deployed DM = 9 rows (= A/B QA baseline). `.xdm.catalog` re-export DONE 09:43 (user, verified byte-for-byte) → commit `a53bfb96` → PR #1141 opened 09:50.
- ~~Routed comments ready to post~~ — ALL SIX POSTED 2026-10-20 (user), recorded in the plan as Q22–Q27 with verbatim texts and anchors. Confirmed live in the 09:52 comment re-sync: FSD anchors (Scenario-1 title, QC-fail DFF sentence, Q1-thread reply) + mapping cells ADDL_SUBLINES!D36, LINES!D173, ADDL_SUBLINES!D23. The 09:00 invisibility was Drive comments API lag, not missing posts. **Answers 2026-10-20 (14:01 sync):** Q22 ANSWERED (warranty price always fixed, no discount — classifier safe); Q27 ANSWERED (§2.3 bullet stale, Aruna updated the FSD body to the EFF-linkage wording — no DM impact); Q9 re-confirmed (warranty .2/.3 = replacement's pickup completion — item 7 as built). Q23/Q24/Q25/Q26 pending.
- ~~Round-3 review panel~~ — DONE 2026-10-20: 12/12 seats, zero blockers, 15 findings; user dispositions executed the same day (merge + A/B above).
- QA-23 to QA-31 added to the plan (round-2 scenarios); QA-25 and QA-31 are already proven by the merged A/B. QA-23 needs a fresh multi-line delivery (already-loaded rows never re-emit).
- Guillermo warranty-return QA data: fresh partials + one full-refund case with completed OMG credit memos. Blocks QA-11/12/14(full); newest dev1 CM is 2026-08-03.
- QA-22 live proof: OM (Ranjeeth) completes the pickup task on 353's replacement line; the 353 char5 mixed-semantics flag rides with that ask.
- Q18 probe: orchestration group stays ACTIVE on closed orders — empirical check rides with QA.
- Deploy order: 3003 (OTCM-146384, Guillermo, in Review) loads first, then 3001 PoD (confirmed by Aruna 2026-10-15).
- Prod gates: OM prod pickup-task setup timing; explain plans on stage (unwindowed CTEs).

## Artifacts

- FSD + comments: `integrations/RMCS-I-3001/docs/drive/RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.md`
- Review pack: `oracle-integration-cloud/tmp/otcm146798_review/` (diff, briefs, round1 reports, consolidated, questions_to_route)
- A/B harness artifacts: run outputs cleaned 2026-10-20 (results recorded in Evidence); harness scripts kept at `monocle_integrations/tmp/build_*.py` + `compare_r2_ab.py` for the QA-22 rerun
- Skills: fusion-sql (RP_ARB usage), bip-catalog-sync (upload + round-trip verify executed both pods)
- Catalog swap artifacts: `oracle-integration-cloud/tmp/otcm146798_r3_impl/catalog_swap/{dev1,stage}/` (backups, orig, edited, round-trips)
