# OEH-94147 — WMS-I-1006: all-SF ship-confirm file timed out in the tracking-reference step
- **Ticket**: https://warbyparker.atlassian.net/browse/OEH-94147
- **RICE**: WMS-I-1006
- **Repos**: monocle_integrations
- **Status** (as of 2026-11-23): RESOLVED (Done) in Jira 2026-11-23 — terminal; this file is FROZEN. PR #2956 MERGED (`a7c3f2839`); prod tag `v1.0.43` pushed and green through stage. Residual: the prod apply waits at the CD pipeline's manual-approval gate (held since 2026-11-23 20:01Z); approving it activates the fix and the split flag in prod.
- **Plan**: — (no plan file; incident-driven ticket)

## Outcome
- SaveTrackingReferenceStep no longer queries Oracle for SF fulfillment requests. SF references store with empty order fields.
- An all-SF file finishes in ~1.6 s with zero Oracle calls. The old build spent 44.4 s on one FR's report call and skipped the row.
- OMG files keep the pre-change path. Verified unchanged on stage.

## What shipped
- [monocle_integrations #2956](https://github.com/WarbyParker/monocle_integrations/pull/2956) — SF tracking-reference resolution skip + WMS-I-1006-split-by-shipment flag enabled in prod config. **MERGED** 2026-11-23 (`a7c3f2839`, squash, CI green on the merge commit). The fix and the flag activate on the next prod tag deploy.
- Stage tag `vstage468` (commit `4d2c3d16d`, = PR #2956 head) — deployed 2026-11-23 17:04Z for the evidence round (CircleCI run 3df9be1c-a9fc-4679-9fa1-0f7ba2195bfa).
- Prod tag `v1.0.43` (`[OEH-94147] WMS-I-1006 skip Oracle FR resolution for SF sales orders`, ships only `a7c3f2839`) — pushed 2026-11-23 19:53Z. CD pipeline (run 7aef4f9e-d138-4427-92cb-cdc80754401f): package, stage apply, stage health checks and prod plan all green; prod apply pending at the manual approval gate (held 20:01Z).

## Decisions
### Functional clarifications (Q&A)
- None. OEH auto-error ticket; no functional questions raised.

### Design decisions (ours)
1. SF candidates store with empty `sales_order_number`/`order_type`/`line_type` instead of skipping. The OM-I-3015 tracker sync consumes them without Oracle order data.
2. OMG path unchanged by design. The step still batches all OMG FRs into one report call.
3. The split-by-shipment flag flip rides PR #2956 as config-only. It needs no test or evidence of its own (Luis, 2026-11-23, chat).
4. S1 replayed a pre-existing stage split file directly into `In/`. The part-A SFTP backup/split step was not re-run (Luis, 2026-11-23, chat); the PR does not touch part A.
5. S2 used an organic stage file instead of a crafted fixture (Luis, 2026-11-23, chat). It covers the real end-to-end OMG path.

## Evidence
- 2026-11-23 17:04–17:15 UTC, stage events Lambda (vstage468) → evdi-test. S1 all-SF replay (shipment `LV0DW45RS`, request `14018f3a-54a6-4c55-a6ee-23492ae15671`): 200 in 1,590 ms, row stored with empty order fields, zero Oracle calls. Pass.
- S2 organic OMG file (shipment `S0ZM7QSH57`, request `0d574452-ced1-4b37-a234-b0857aa6a08d`): report called twice (both pre-existing call sites), resolved `TR4E8601DW`, stored with `WP_B2C` fields. Pass.
- Baseline A/B: the same FR on the old build (2026-11-22) spent 44.4 s on its report call and skipped the row.
- Jira run-evidence comment 989665 (posted 2026-11-23) with 3 attachments: S1/S2/baseline raw CloudWatch pulls.

## Test data
- S1: pre-existing stage split file (SF shipment `LV0DW45RS`, facility `LLAS`), replayed as-is. Contains test-customer ship-to data; cited by S3 key only (`vendors/Manhattan/WMS-I-1006/Archive/11232026/`).
- S2: organic stage order `S0ZM7QSH57` (facility `LSLO`) from an automated stage process.
- Comparator row: OMG shipment `S0ZACACYQY`, written by the old build pre-deploy.

## Open items
- ~~QA verification of the run evidence~~ — RESOLVED 2026-11-23: QA moved the ticket to Resolved on comment 989665.
- ~~PR #2956 merge + prod tag~~ — MERGED 2026-11-23 (`a7c3f2839`); tag `v1.0.43` pushed. Remaining: approve the prod apply at the CD pipeline's manual gate. The apply activates both the fix and the split flag in prod.
- Three follow-up ticket drafts (file only, never filed): mixed-file SF storage, deterministic tracking-reference ids, blank-FR storage — `monocle_integrations/tmp/oeh94147_followup_*.md`.

## Artifacts
- Evidence draft: `monocle_integrations/tmp/oeh94147_qa_evidence_comment.md`; raw pulls: `monocle_integrations/tmp/oeh94147_evidence/`.
- Jira: comment 989665 on OEH-94147 (attachments 372846/372847/372848).
