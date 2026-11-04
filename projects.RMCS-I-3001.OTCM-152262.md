# OTCM-152262 — RMCS-I-3001: resolve the RMI text source_line_id in the PoD DM (stage ORA-01722)

- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-152262
- **RICE**: RMCS-I-3001 (follow-on of OTCM-146798 / PR #1141)
- **Repos**: oracle-integration-cloud (DM only)
- **Status** (as of 2026-11-04): **DONE** (QA moved it 2026-11-04 06:15 ET, resolution Done). PR #1181 stays open, stacked on #1141 — merges at prod promotion. **This file is frozen.**
- **Plan**: [projects.RMCS-I-3001.OTCM-152262.plan](projects.RMCS-I-3001.OTCM-152262.plan.md) — verbatim archive. The working journal rode in `projects.RMCS-I-3001.OTCM-146798.plan.md` (same stream); the archive was copied at wrap-up.

## Outcome

- The PoD data model resolves the replacement EFF's text `source_line_id` (char5) and the Warranty FR-id (char1) through lookups instead of `TO_NUMBER`, ending the stage ORA-01722 failures that killed the 2026-10-30 run of the 17 orders.
- Two hardening fixes shipped in the same PR: pickup-sourced warranty PoDs wait for a terminal covered member (`8754dcc4`), and delivery-sourced covered members count complete only once a delivery date exists (`76eb6e55`).
- QA passed on stage: all 7 acceptance criteria green with disclosed boundaries, evidence posted as Jira comment 978153.

## What shipped

- **[PR #1181](https://github.com/WarbyParker/oracle-integration-cloud/pull/1181) OPEN**, stacked on #1141 (itself on #1105): `WP_RMCS_PROOF_OF_DELIVERY_DM.sql` + paired `.xdm.catalog`. Head `76eb6e55`. Merges at prod promotion, after RMCS-I-3003 (OTCM-146384).
- Live deploy 2026-11-03: both pods re-uploaded via CatalogService `updateObject`; round-trip CDATA byte-equal to the PR `.sql` (sha256 `c7cf84dd`) on dev1 AND stage; the PR's `.xdm.catalog` re-export (dev1) carries the same bytes.
- Guillermo's 5-thread review closed 2026-11-03: char1 confirmed by FSD ruling (kept whole), DELIVERY-gate fixed in-PR, canceled-member hold spun off to OTCM-153073, ORA-01722 confirmed deliberate fail-loud, timing cited from the saved A/B log.

## Decisions

### Functional clarifications (Q&A)

1. The Warranty EFF char1 carries the frame's FR id (Aruna, FSD comment 2026-11-03) — confirms the char1-as-FR-id resolution the PR implements.
2. A covered line canceled before shipping must NOT hold the warranty PoD; the warranty PoD goes out with the latest delivered member's date; an all-canceled family keeps holding (Aruna ruling D3, FSD thread 2026-11-03 ~19:48 UTC) — shipped as follow-up OTCM-153073, not in PR #1181 (user scope decision 2026-11-03).

### Design decisions (ours)

1. char5 resolution looks up the original's DOO line by order number + text `source_line_id`. Unmatched text fails loud (ORA-01722 kept on purpose); unmatched numeric converts and silently matches nothing.
2. char1 resolution mirrors char5 (FR-id family prefix), fail-closed on legacy numeric shapes. The dev1 order-275 A/B delta is the intended semantic change, not a regression.
3. Pickup family-gate (`8754dcc4`): a pickup-sourced warranty PoD waits until every covered family member reaches a terminal state.
4. DELIVERY-gate (`76eb6e55`): on delivery-sourced order types a covered member counts complete only once its delivery date exists. Guillermo review finding; a stage probe found 13 held families, none ever loaded, so nothing to reprocess.
5. QA evidence posted as ONE comment with per-item pod annotations in parentheses (user decision 2026-11-03, reversing the two-comment split draft).
6. AC3 verified probe-only (user decision 2026-11-03): no live unmatched text char5 exists pod-wide (157/157 resolve), so the fail-loud path was exercised by replaying the DM's exact COALESCE expression.

## Evidence

- QA evidence comment **978153** on OTCM-152262 (2026-11-03): all 7 ACs pass with 5 disclosed boundaries. Stage runs S1 (fixture TQ8TPR00Q4 → 204, 1 row), S2 (the 17 orders → 204, 37 rows, 0 errors), S6 (wholesale order 36 → 204, 1 row, PoD 2026-10-09); S3 idempotency controls (0 rows on re-extract); S4 AC3 fail-loud probes; S5 dev1 A/B (25/27 identical, 2 old-only on synthetic order 275, 0 new, 0 diffs; saved-log timing 10.1s → 4.9s).
- Downstream chain verified per load: VRMPRCBLS → IdentifyContractObligation → RecogRevForCustContracts all SUCCEEDED; 38/39 rows advanced to `CREATE_ASE_PROCESSED` by the 2026-11-03 20:50 UTC re-pull.
- A 4-seat audit panel reviewed the draft before posting (live re-verify, source cross-check, SOX quality, adversarial); ~15 fixes applied (status-drift lifecycle wording, timing-artifact swap, owner-accepted boundary 3, as-of stamps, drift notes).

## Test data

- Skill: `rmcs-test-data`. Integration assets: `integrations/RMCS-I-3001/`.
- Stage fixture pair TQ8TPR00Q4 (QC-failed original) / AAZH4J44HS ($0 remake, text char5 `X2V0K1ZP`).
- The 17 stage orders from the failed 2026-10-30 run (listed in the QA comment).
- Stage wholesale order 36 (WP_B2B_WHOLESALE, FULFILLMENT date source).
- dev1 synthetic order 275 (legacy numeric char1).

## Open items

- PR #1181 merges at prod promotion (stack #1105 → #1141 → #1181; deploy order after RMCS-I-3003 OTCM-146384).
- OTCM-153073 (canceled covered lines release) — blocked-by this ticket, now unblocked.
- Prod timing flag: if OTCM-152262 promotes before OTCM-153073 ships, prod holds accumulate with no reprocess path (flagged 2026-11-03).
- Boundary-3 follow-up: the first organic whole-order replacement on stage validates the char5-NULL path live (owner-accepted 2026-11-03).

## Artifacts

- QA evidence draft: `oracle-integration-cloud/tmp/otcm152262_qa_evidence_comment.md` (posted verbatim as comment 978153).
- FSD + comments: `integrations/RMCS-I-3001/docs/drive/RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.md`.
- Worktree: `oracle-integration-cloud/tmp/otcm152262-wt/` (branch `OTCM-152262-rmcs-i-3001-pod-source-line-id`).
- Evidence pack (ephemeral): `/tmp/otcm152262_qa/` — CloudWatch logs, A/B buckets, probes; DM upload rollback originals at `/tmp/otcm152262_dm_upload/` (keep until the PR merges).
- Plan archive: [projects.RMCS-I-3001.OTCM-152262.plan](projects.RMCS-I-3001.OTCM-152262.plan.md).
