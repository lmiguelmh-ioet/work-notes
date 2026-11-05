# OTCM-153073 — RMCS-I-3001: release the warranty PoD when a covered line is canceled pre-shipping
- **Ticket**: https://warbyparker.atlassian.net/browse/OTCM-153073
- **RICE**: RMCS-I-3001
- **Repos**: oracle-integration-cloud
- **Status** (as of 2026-11-05): ticket in QA; PR #1184 open in native GitHub stack #1182 (#1105 ← #1141 ← #1181 ← #1184), CI green; review round 1 answered and closed (qty-0 case CLOSED — no follow-up; closing comment 979446); QA passed on dev1, evidence posted (comment 979116); stage DM parity DONE after the pod recovery; AC6 stage e2e leg awaiting user's go
- **Plan**: `monocle_integrations/.cursor/plans/rmcs-i-3001_pod_canceled_covered_line.plan.md` (frozen copy: `projects.RMCS-I-3001.OTCM-153073.plan.md`)

## Outcome
- The PoD data model releases a family's warranty .2 PoD and U record when a covered line is canceled before shipping.
- The family releases on the surviving delivered member's date. The U record's end date stays delivery + 365.
- An all-canceled family still holds with no error. Post-shipping returns and every other family behavior stay byte-identical.

## What shipped
- PR [#1184](https://github.com/WarbyParker/oracle-integration-cloud/pull/1184) — open, stacked on #1181, merges at prod promotion. `WP_RMCS_PROOF_OF_DELIVERY_DM.sql` + paired `.xdm.catalog` (commit da8846cc, +49/−16, 7 hunks).
- dev1 deploy 2026-11-05 — comment-final DM text live via CatalogService `updateObject`; re-downloaded CDATA byte-equals the committed .sql (sha256 658da45d272b); report parses.
- stage deploy 2026-11-05 ~22:10 UTC — comment-final text live via targeted two-CDATA splice + `updateObject`; re-downloaded SQL span byte-equals the committed .sql (658da45d272b); report smoke parses. Both pods at parity.
- Review round 1 (2026-11-05) — Bugbot's missing-catalog-pair finding answered (false positive; the commit carries both files). Guillermo's qty-0 change-order finding confirmed on dev1, ruled on by functional (two FSD rulings), and CLOSED with no code change (closing reply discussion_r4486590083).

## Decisions

### Functional clarifications (Q&A)
1. Must the warranty PoD release when a covered line is canceled pre-shipping? → Yes, with the surviving delivered member's date — functional (Aruna), FSD ruling thread, 2026-11-04.
2. Is post-shipping cancellation possible? → No; a shipped line returns via RMA — Aruna, FSD ruling thread, 2026-11-04.
3. Two proceeding assumptions posted to Aruna (FSD ruling thread, 2026-11-05): OM never cancels a QC-failed line that received a replacement; an all-canceled family keeps holding. ANSWERED 2026-11-05: (1) confirmed — OM never cancels a QC-failed covered line at all (marks QC fail, creates a replacement order); (2) unobjected, stands.
4. Third assumption posted (FSD thread, 2026-11-05, from Guillermo's PR review): a change order setting a covered line's quantity to 0 counts as a pre-shipping cancel. ANSWERED 2026-11-05 (reframe): OMG zeroes the warranty line with the covered line (related lines), so nothing ships/bills, no contract forms, and no PoD is due. Mixed-sequence clarification posted the same day. CLOSED 2026-11-05 (Aruna, verbatim): "In Order Management, order orchestration is structured to bill the warranty line only after the covered line has shipped, ensuring both lines are billed together." A billed warranty implies a shipped covered line, so a billed-warranty family is always post-shipping and its PoD flows through the delivered path — the mixed sequence cannot arise. No follow-up ticket, no code change.

### Design decisions (ours)
1. Cancel exclusion keyed on "no fulfill row reached a terminal state" — a post-shipping cancel keeps the member on today's path, byte-identical.
2. Cancel re-selection rides the family's last-update channels plus the existing backfill arm — no new selection arm.
3. Pickup channels keep explicit exclusion wraps — the QC redirect supplies pickup dates without a terminal row (fail-closed, load-bearing).
4. QC-failed-then-canceled: no code change; documented as a silent-hold boundary (evidence Boundary 6). Standing constraint if it is ever implemented: pod-date arm only, because the last-update arm is GREATEST-NULL-poisoned.
5. Ship as a fourth stacked layer on the PoD DM chain (#1105 ← #1141 ← #1181 ← #1184), merging only at prod promotion.

## Evidence
- QA-1/QA-2 full-extract A/B 2026-11-04 (dev1+stage, 5 windows, 2026-06-01→run-date): old vs new DM byte-identical, 5/5 on both pods.
- QA-3 dev1 e2e 2026-11-04 (TestCP1, ott Lambda request 7afe10fb-a17a-4c61-a3d4-3c07412f2a2a): HTTP 204; .2 dated T1=2026-11-04; U on subline 3.3 DEFERRED, end 2027-11-04 (T1+365); FBDI ESS 117206105; re-extract 0 rows.
- QA-12 dev1 e2e 2026-11-05 (TestCP3, ott Lambda request 6d1d2ca3-af47-4fc6-8c09-8d0393d36c02): HTTP 204; 5 rows; U landed with SRC_ATTRIBUTE_DATE1=2027-11-05 (T1+365); FBDI ESS 117208796; re-extract 0 rows.
- Synthetic harness matrix QA-4..QA-11 and QA-13: 9/9 pass.
- QA evidence comment POSTED 2026-11-05 (Jira comment 979116 on OTCM-153073); source draft at `oracle-integration-cloud/tmp/otcm153073_qa_evidence_comment.md`.
- Stage e2e leg (AC6): POSTPONED by the fa-evdi-test outage.

## Test data
- Skill: `rmcs-test-data`.
- dev1 fixtures: TestCP1 (header 300000913502149, contract 55049, invoice 60106); TestCP3 (header 300000913635069, contract 55072, invoice 61106).

## Open items
- Stage e2e leg (AC6) — unblocked (pod recovered 2026-11-05 ~17:05 EST); awaiting user's go, then posts as its own stage QA comment.
- qty-0 case CLOSED 2026-11-05, no follow-up ticket — closing comment POSTED on the ticket (Jira 979446) and the closing reply POSTED on Guillermo's PR thread (discussion_r4486590083).
- PR #1184 merge — waits on prod promotion of the stack (#1105 ← #1141 ← #1181).

## Artifacts
- FSD: https://docs.google.com/document/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/edit (ruling thread: `disco=AAAB_Ztc5xA`)
- Skills used: `bip-catalog-sync`, `fusion-sql`, `om-order-lifecycle`, `rmcs-test-data`
- Review scratch: `/tmp/otcm153073_review/` (pre-opening panel, 2026-11-05)
