## CM-I-3004 - payout bank statement import

- additional info about cash reconciliation report from Providers (Stripe, Paypal, Affirm)
	- [projects.cash-reconciliation](projects.cash-reconciliation.md)
- OIC: WP Bank Statements Callback Integration
```
'BANK-STATEMENTS-CALLBACK'
lookupValue('WP_CMN_INT_UTIL_LKP', 'IntegrationRICEId', VAR_RICE_ID, 'RESTApiURI', '')
curl --verbose -X POST https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/{import-verification-uri} \ -H "Authorization: [authorization-value]" \ -H "Content-Type: application/json" \ -d '{ "import_event_response" : { "status" : "SUCCEEDED", "jobs" : [ { "id" : "12345", "name" : "Load Interface File for Imports", "status" : "SUCCEEDED", "document_name" : "EDI835-2025-12-16-CECEOB_Warby Parker_12162025_f50-Reimbursement.zip" }, { "id" : "98765", "name" : "Import Bank Statements from a Spreadsheet", "status" : "SUCCEEDED", "document_name" : null } ] }, "total" : 10 }'
```

---

## IN-I-2060 - OMA file dispatcher
- ?
- PRs:
	- Integration test: https://github.com/WarbyParker/monocle_integrations/pull/1641


---

## SNS Adapter
- 



---
## MFG-I-3021 - material issue

- 4 days for main integration
	- [20260120: QA testing](day/day-20260120.md)
	- [20260119: PR API test](day/day-20260119.md)
	- [20260118: PR main monocle integration](day/day-20260118.md)
	- [20260115: start ticket](day/day-20260115.md)
- 4 days for OIC and skeleton
	- [20260114: PRs: OIC integration + Basic API skeleton](day/day-20260114.md)
	- [20260109: start ticket OIC integration](day/day-20260109.md)
- payloads: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&pref[…]ors/Manhattan/MFG-I-3021/Archive/&showversions=false
	- en Backup se guarda una copia del payload "original", haya finalizado o no con errores
	- en Archive se guarda el resultado del API si es exitoso
	- en Error se guarda el resultado del API si es fallido
- tickets: 
	- https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22
- original tickets: 
	- https://warbyparker.atlassian.net/issues?jql=textfields%20~%20%22MFG-I-3021%22%20AND%20reporter%20!%3D%20633e0a9afedc6169aed9dc30
	- https://github.com/WarbyParker/monocle_integrations/pull/1600


## S3-driven flows

```
## Similar S3-triggered integration tests

### 1. AP-I-1048 (Case Optics Invoices) — most similar

- File: test/integrations/wp_ap_invoices/wp_ap_i_1048_case_optics_invoices_to_oracle_inbound/oic_integration_1048_case_optics_invoices_to_oracle_test.py

- Pattern: Upload file → Trigger OIC → Wait → Verify file moved → Verify business results

- Key features:

- Uses check_invoice_file_exists_in_s3 to verify file was moved

- Verifies business outcomes (invoice created, PO status)

- Uses oic_run_scheduled_integration to trigger processing

### 2. PO-I-2008 (In-House Optical Labs PO)

- File: test/integrations/wp_po_i_2008_po_in_house_optical_labs_inbound/oic_integration_2008_lslo_in_house_optical_labs_inbound_test.py

- Helper: test/integrations/wp_po_i_2008_po_in_house_optical_labs_inbound/_common.py

- Pattern: Create file → Upload → Trigger OIC → Verify PO created → Verify file archived

- Key features:

- Uses _common.py for shared helpers

- Uses s3_prefix_exists to check archive location

- Organization-specific tests (LSLO, LLAS variants)

### 3. IN-I-2047 (Occuco PO Receipt)

- File: test/integrations/wp_in_i_2047_occuco_to_oracle_po_receipt/oic_integration_2047_occuco_lslo_to_oracle_po_receipt_test.py

- Helper: test/integrations/wp_in_i_2047_occuco_to_oracle_po_receipt/_common.py

- Pattern: Create PO → Create ASN → Upload receipt file → Trigger OIC → Verify receipt → Verify file archived

- Key features:

- More complex setup (creates PO and ASN first)

- Verifies business state (PO status = "CLOSED FOR RECEIVING")

- Uses s3_prefix_exists for archive verification

### 4. GL-I-1023 (Springfield Journal)

- File: test/integrations/wp_gl_i_1023_springfield_to_erp_journal_inbound/oic_integration_1023_springfield_to_erp_journal_test.py

- Helper: test/integrations/wp_gl_i_1023_springfield_to_erp_journal_inbound/_common.py

- Pattern: Create journal file → Upload → Trigger OIC → Wait → Verify journal batch created → Cleanup

- Key features:

- Includes cleanup (delete_journal_file_from_s3)

- Verifies complex business outcomes (journal batches)

- Uses helper functions in _common.py
```
