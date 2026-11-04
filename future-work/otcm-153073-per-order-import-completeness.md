> Parked follow-up from OTCM-153073 (RMCS import-verification hardening). Filed
> as OTCM-153178 on 2026-11-04 without the user's review (agent error — see
> `jira-ticket-drafting` rule) and deleted the same day. The text below is a
> reconstruction of the adversarially reviewed design; the original wording was
> lost with the ticket. Re-verify every claim against the current repo before
> filing.

# Summary

RMCS-I-3001: fail import verification when an imported order has no contract status rows

# Description

## Context

`monocle_integrations` runs the RMCS-I-3001 PoD upload: it builds the FBDI file
from the proof-of-delivery rows, submits it through `erpintegrations`
(`importBulkData`), and OIC calls back into
`POST /rmcs/import-verification-callback`. The callback runs
`VerifyCustomerContractStatus`
(`monocle_integrations/_domain/_integrations/_wp_import_verification_callback/_steps/_verify_customer_contract_status.py`):
it reads the customer contract status report (rows of `vrm_source_doc_lines`)
filtered by the upload's load job and requires every returned row to be
`SUCCESS`.

OTCM-153073 shipped the status-mapping fix only. A report returning **no
rows** for the load still passes verification vacuously: a load that wrote
nothing at all looks identical to a full success. The upload skips the FBDI
import when its extract is empty, so a submitted load that yields zero rows
means a write or report-parameter mismatch, not a legitimate empty run. The
zero-row guard was cut from OTCM-153073 as speculative; whether it is worth
its detection value is decision D1 below. The per-order case is the larger
hole either way.

## Problem

A load can import rows for some orders and silently skip others, and still
return rows — verification passes while one order's contracts were never
created or updated. The check today is "rows exist and all are SUCCESS"; it
never verifies that every order the upload actually carried produced a row.

The expected-order set is NOT the request's order list:

- The upload request accepts `sales_order_numbers` OR a `from_date`/`to_date`
  window, so in a date-range run there is no explicit list at all.
- A requested order may legitimately produce no PoD rows (not delivered yet).
  Failing the upload for that would fail valid runs.

So the expected set must be the orders the generated interface rows actually
carried — the imported set, captured at upload time.

## Proposal

1. **Persist the expected set before submit.** When the upload builds its PoD
   interface rows, persist the distinct order numbers of those rows, keyed by
   the upload's request id (the `oic_instance_id` that already round-trips
   through `encode_rmcs_fbdi_document_name` /
   `parse_rmcs_fbdi_document_name`). A persistence failure fails the upload —
   fail-loud, same as the rest of the intake.
2. **Check the set in the callback, scoped to RMCS-I-3001 only.** In
   `VerifyCustomerContractStatus`, for I-3001 requests, join the persisted
   expected orders against the order numbers on the report rows and fail
   verification listing each expected order with no row. The step is shared
   with RMCS-I-3003 — I-3003 behavior must not change.
3. **Key-column prerequisite.** Confirm on stage that the report's
   `ORDER_NUMBER` is populated for I-3001 rows. If it is blank, fall back to
   `DOCUMENT_LINE_ID` (the order number is encoded in the document line) and
   record the fallback in the ticket.
4. **Batch-block consequence.** One missing order fails the whole load's
   verification, same as one FAILED row does today. Name that consequence in
   the ticket so functional signs it off.
5. **Retention.** Expected-set records expire after 30 days, matching the
   retention pattern of the surrounding RMCS staging artifacts.
6. **D1 — whole-load case.** Decide whether verification also fails when the
   report returns zero rows for the load. The upload skips the FBDI import on
   an empty extract, so zero rows implies a mismatch; the guard detects that
   bug class but guards no legitimate flow. Record an explicit accept/reject
   with the reason, priced separately from the per-order work.

## Acceptance criteria

1. The distinct order numbers of the imported PoD rows are persisted, keyed by
   request id, before the ESS submit; a persistence failure fails the upload.
2. The expected-order check runs only for RMCS-I-3001 requests. Tests prove
   RMCS-I-3003 behavior is byte-identical to before.
3. Verification fails and names every imported order with no contract status
   row; the all-present case keeps its current behavior. Unit tests cover
   both at 100% coverage per the repo gate.
4. Stage evidence attached to the ticket shows `ORDER_NUMBER` populated on the
   report rows for an I-3001 load — or documents the `DOCUMENT_LINE_ID`
   fallback and keys the check on it.
5. Expected-set records are reaped after 30 days.
6. The ticket records an explicit accept/reject decision on the whole-load
   zero-row guard (D1), with the reason.

## References

- Incident and fix: OTCM-153073 comment thread (stage verification,
  2026-11-04) and its PR on `WarbyParker/monocle_integrations`.
- Crash ticket from the same verification: OTCM-153172.
- Verification step: `monocle_integrations/_domain/_integrations/_wp_import_verification_callback/_steps/_verify_customer_contract_status.py`
- Request-id round-trip: `encode_rmcs_fbdi_document_name` /
  `parse_rmcs_fbdi_document_name`.

## Out of scope

- Any RMCS-I-3003 behavior change.
- Post-Identify verification — that is the companion draft
  [otcm-153073-identify-submission-alerting.md](otcm-153073-identify-submission-alerting.md).
