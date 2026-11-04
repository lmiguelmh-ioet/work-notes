> Parked follow-up from OTCM-153073 (RMCS import-verification hardening). Filed
> as OTCM-153179 on 2026-11-04 without the user's review (agent error — see
> `jira-ticket-drafting` rule) and deleted the same day. The text below is a
> reconstruction of the adversarially reviewed design; the original wording was
> lost with the ticket. Re-verify every claim against the current repo before
> filing.

# Summary

RMCS: alert when verified loads are not identified as contracts

# Description

## Context

After import verification passes, monocle submits the **Identify Customer
Contracts** ESS job so Oracle turns the imported source-document lines into
revenue contracts. The Identify submit is ledger-scoped: it takes the ledger
and process parameters, and nothing ties the submission to the load that
triggered it (verified against the submitter code).

Three integrations submit Identify: RMCS-I-3001 (PoD upload), RMCS-I-3002
(credit memo flow, an Identify-only path), and RMCS-I-3003 (returns).

The 2026-11-04 incident: the RMCS-I-3001 import-verification callback crashed
with `KeyError: 'UPDATE_PROCESSED'` **after** import verification had
succeeded, so Identify was never submitted for that load. Nothing detected the
gap — a teammate (Vijay) submitted Identify manually. The error flow opened
OTCM-153172, but that ticket tracked the crash; no check exists for
"verification passed, Identify never went out".

## Problem

A **missing** Identify submission produces no event at all. Any design that
listens for a completion signal (the `rmcs_job_callback_url` callback) cannot
catch a submission that never happened — there is no job to call back about.

The inverse signal is unusable too: because Identify is ledger-scoped, a
legitimate run can identify **zero** new contracts (concurrent loads, or a
previous run just processed the same ledger). "Zero contracts identified" is
not a failure. The only reliable signal is: **a load passed verification and
no Identify submission was recorded for it within the SLA.**

## Proposal

1. **Persist a submission record at submit time.** All three Identify
   submitters (I-3001, I-3002, I-3003) record: the ESS job id, the RICE id,
   the load/import/request ids the submission serves, and the submission
   timestamp.
2. **SLA check on the missing-submission gap.** A periodic check flags any
   load that passed import verification but has no Identify submission record
   within the SLA, and raises an alert naming the RICE id and load. This is
   the exact 2026-11-04 failure mode.
3. **Concurrency exemption.** A submission that identified zero contracts is
   NOT an alert — only the absence of a submission is. (Ledger-scoped runs
   legitimately yield zero under concurrent loads.)
4. **Rollout note.** `rmcs_job_callback_url` is empty in `prod.yml` today;
   decide whether enabling the completion callback in prod is part of this
   work or a separate config change, and record the decision on the ticket.

## Open questions

- **Q1 — SLA bound:** how long after verification passes does a missing
  submission become an alert (minutes, hours)?
- **Q2 — alert channel:** OEH ticket through `wp_error_ticket_creation`,
  Slack, or New Relic?
- **Q3 — sweep owner:** monocle is event-driven with no scheduler today — a
  new EventBridge-triggered run of the Lambda, or an external monitor querying
  the submission records?
- **Q4 — retention:** how long submission records live (align with the 30-day
  pattern used for RMCS staging artifacts?).
- **Q5 — prod callback:** is enabling `rmcs_job_callback_url` in prod in
  scope, or a separate config ticket?

## Acceptance criteria

1. Every Identify submission — across RMCS-I-3001, RMCS-I-3002, and
   RMCS-I-3003 — persists a record correlating the ESS job id to the
   triggering RICE id, load/import ids, and request id.
2. A load that passed import verification with no submission record within the
   SLA raises an alert naming the RICE id and the load.
3. A submission that identified zero contracts raises no alert; a test covers
   the exemption.
4. Unit-test coverage stays at 100% per the repo gate (`make check-coverage`).
5. The ticket records the prod decision for `rmcs_job_callback_url`.

## References

- Incident and fix: OTCM-153073 comment thread (stage verification,
  2026-11-04) and its PR on `WarbyParker/monocle_integrations`.
- Crash ticket from the same verification: OTCM-153172.
- Callback route: `POST /rmcs/import-verification-callback`
  (`monocle_integrations/_api/_test/_rmcs_import_verification_callback_routes_api_test.py`
  covers both I-3001 and I-3003 scenarios).
- Verification step: `monocle_integrations/_domain/_integrations/_wp_import_verification_callback/_steps/_verify_customer_contract_status.py`

## Out of scope

- Fixing the crash itself — shipped under OTCM-153073.
- Per-order completeness inside import verification — that is the companion
  draft
  [otcm-153073-per-order-import-completeness.md](otcm-153073-per-order-import-completeness.md).
- Changing what Identify submits (ledger scoping stays as-is).
