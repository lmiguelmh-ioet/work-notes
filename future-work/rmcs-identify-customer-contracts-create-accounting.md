# FILED as OTCM-160175 (2026-11-25): https://warbyparker.atlassian.net/browse/OTCM-160175
# Both open questions answered in the 3001 FSD thread (Aruna, 2026-11-25).

**Title:** RMCS-I-3001: submit Identify Customer Contracts with Create Accounting = Yes and Summary report style per the FSD

**Project:** OTCM · **Type:** Story · **RICE:** RMCS-I-3001

## Context

The RMCS-I-3001 FSD prescribes the Identify Customer Contracts job parameters in its "Identify customer contracts" section. The updated screenshot (synced 2026-11-25) sets Create Accounting = Yes and Report Style = Summary.

The integration submits the same job with Create Accounting = No and Report Style = Detail. The adapter `_erp_identify_customer_contracts_action.py` hardcodes these values. A code comment records the reason: accounting stays on its own scheduled cadence. Live proof on TEST (2026-11-24): the integration-submitted ESS request 128238851 carried arguments `300000003994590,D,2026-11-30,D,N,N,N,N,#NULL`.

The two values change what the job does. With Create Accounting = Yes and Draft mode, the job creates draft accounting at identification time. With No, accounting waits for the scheduled cadence. The General Ledger flags stay No on both sides. The remaining parameters match the FSD. This divergence caused confusion during the 2026-11-24 warranty PoD runs.

The ESS codes are confirmed. Manual UI submissions on TEST carried `S` for Summary and `Y` for Create Accounting: ESS 128055584 (ext.vbellurkar, 2026-11-02), ESS 128052651 and 128002578 (ext.abhairapuneni, 2026-10/11), arguments read from `ess_request_property`.

The job takes nine parameters. Two change. Seven already match the FSD.

| Pos | Parameter | Integration today | FSD | Change? |
|-----|-----------|-------------------|-----|---------|
| 1 | Ledger | 300000003994590 (WP US USD PL) | WP US USD PL | No |
| 2 | Accounting Mode | D (Draft) | Draft | No |
| 3 | Accounting End Date | Computed current month-end | 08/31/2026 — illustrative (open question 1) | No |
| 4 | Report Style | D (Detail) | S (Summary) | Yes |
| 5 | Create Accounting | N (No) | Y (Yes) | Yes |
| 6 | Process Errors Only | N | N | No |
| 7 | Transfer to General Ledger | N | N | No |
| 8 | Post in General Ledger | N | N | No |
| 9 | General Ledger Batch Name | #NULL | #NULL | No |

Change: set `_CREATE_ACCOUNTING` to `"Y"` in the adapter. Rename `_REPORT_STYLE_DETAIL` to `_REPORT_STYLE_SUMMARY` and set it to `"S"`. Rewrite the code comment: state the new intent and the dedup rationale from Q2's answer, keep the 9-position parameter block, cite no document. Update the paired unit test. No data-model, FBDI, or mapping change. No other adapter submits this job. The import verification callback stays the only submission path.

Blast radius: the import verification callback submits this job after every successful RMCS import of three flows: RMCS-I-3001 (PoD), RMCS-I-3002 (billing), and RMCS-I-3003 (contract creation). The post-processor factory maps all three RICE IDs to Identify steps. After deployment, every identified contract in every environment gets draft accounting at identification time. Functional sign-off on the draft-accounting interaction (Q2) gates prod promotion.

## Acceptance criteria

1. Every integration-submitted Identify Customer Contracts job carries the argument string `300000003994590,D,<current month-end>,S,Y,N,N,N,#NULL`. Verify on TEST through `ess_request_property` after a contract-creation run.
2. Draft accounting entries exist for the identified contracts after the run. Functional verifies them in the RMCS accounting review UI on TEST.
3. Contract identification is unchanged. Spot-check one warranty-split order end to end on TEST.
4. Functional confirms on TEST that the scheduled accounting process picks up the drafts without duplicates. Required before prod promotion.

## Rollout

Deploy to stage first. Gather the TEST evidence (AC 1–4). Promote to prod by tag after functional sign-off. Rollback is a revert plus a tag deploy. No feature flag: the FSD prescribes one behavior for every environment, and the evidence gate covers the risk.

## References

- FSD, "Identify customer contracts" section (screenshot updated 2026-11-25): https://drive.google.com/file/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/view
- Adapter: `monocle_integrations/_adapters/_oracle/_erp_integration_service/_actions/_submit_ess_job/_erp_identify_customer_contracts_action.py`
- Submission paths: `monocle_integrations/_domain/_integrations/_wp_import_verification_callback/_steps/_import_verification_post_processor_factory.py`
- Current-behavior evidence (TEST, 2026-11-24): ESS 128238851, arguments `300000003994590,D,2026-11-30,D,N,N,N,N,#NULL`.
- ESS-code evidence (TEST): ESS 128055584, 128052651, 128002578 carry `S` at `submit.argument4` and `Y` at `submit.argument5`.

## Open questions

1. The screenshot shows Accounting End Date 08/31/2026. Assumption: illustrative, not a rule. The adapter keeps the computed current month-end. Confirm with Aruna in the 3001 FSD thread.
2. With Create Accounting = Yes, the identify job creates draft accounting per contract. Confirm with Aruna and Vijay that the scheduled accounting process picks up these drafts without duplicates. Prod-safety gate. Ask in the 3001 FSD thread.
