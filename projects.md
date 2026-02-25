## CM-I-3004

- additional info about cash reconciliation report from Providers (Stripe, Paypal, Affirm)
	- [projects.cash-reconciliation](projects.cash-reconciliation.md)


---

## MFG-I-3021
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
- tickets: https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22


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
