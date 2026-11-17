# Follow-up ticket DRAFT — for functional/Oracle to file (never created by the agent)

**Project:** OTCM (or the functional team's project) · **Type:** Bug · **Component:** Inventory / Transfer Orders

## Summary

Nightly ESS job "Print Cancel Transfer Order Report" (`InvCancelTransferOrderBIPJob`) SUCCEEDS but cancels no short-pick remainder lines on transfer orders

## Description

During OTCM-138123 stage evidence runs (2026-11-16, evdi-test), the ESS job `/oracle/apps/ess/scm/inventory/transferOrders/InvCancelTransferOrderBIPJob` was submitted twice with `CancelOrders=Y`:

- ReqstId 128176045 — CancelDaysFromPast null (job default), TO 26184 parameter
- ReqstId 128176127 — CancelDaysFromPast 0, TO 26184 parameter
- (Ramp/control: ReqstId 128176044 with CancelOrders=N, verified report-only)

Both cancel runs reached SUCCEEDED in ~8–10 seconds, yet the TO's short-pick remainder line (4739780, status "Ready to release", requested qty 2) was never canceled. A third "Ready to release" remainder (4739781 on TO 26182, inside the same org) was also untouched. The job's report output is not retrievable via `downloadESSJobExecutionDetailsRF` (empty), so the selection set cannot be confirmed. The production nightly schedule (scope LSLO/LLAS, ~01:01 UTC, similar short SUCCEEDED durations) may be a silent no-op.

Separately, the manual cleanup path is unsafe: Manage Transfer Orders → line → Cancel Line cancels the ENTIRE TO line including its already-pick-confirmed shipment lines (on 26184, canceling line 8 also canceled Staged shipment line 58783 and zeroed its requested quantity). There is currently no supported way to cancel only the un-picked remainder delta.

## Evidence

- ESS submit + status JSON with exact parameter strings: attached to OTCM-138123 (`ess_cancel_submits_otcm138123.json`); statuses re-pullable via `GET /fscmRestApi/resources/11.13.18.05/erpintegrations?finder=ESSJobStatusRF;requestId=<ReqstId>`.
- Order state re-pullable via `shipmentLines?q=Order='26184'` (evdi-test).

## Acceptance criteria

1. Determine which transfer-order lines the job selects (obtain or reproduce its report output).
2. Explain why ready-to-release short-pick remainders are not selected, or fix the selection.
3. Provide a supported cleanup path for short-pick remainders that does not cancel pick-confirmed shipment lines (or document the correct one).
4. If the prod nightly job is confirmed as a no-op, decide whether to fix or descope it, and update the FSD's remainder-cleanup assumption.
