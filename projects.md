- point to dev1/evdi-test
	- https://github.com/WarbyParker/monocle_integrations/pull/1700/changes
- circle ci
	- https://app.circleci.com/pipelines/github/WarbyParker/monocle_integrations
- create adapter
	- ?
- each one of these projects must have a CURL to the Oracle 


## ON-CALL: MAY18-MAY25
### MAY18
- [x] [OEH-68166](https://warbyparker.atlassian.net/browse/OEH-68166) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|lwwzalLFEfGwnImYdwL8Rw
	- assigned to Josue
- [x] [OEH-68165](https://warbyparker.atlassian.net/browse/OEH-68165) — Error|prod|Non-Payables|IN-I-2017A Fedex Warehouse Transactions Receiving Inbound|82109c93-4314-498b-8934-cf40ad3cfca5
	- on review - rejected
- [x] [OEH-68164](https://warbyparker.atlassian.net/browse/OEH-68164) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|M-yBOFK9EfGsSK3kcBpqQA
	- assigned to Josue
- [x] [OEH-68162](https://warbyparker.atlassian.net/browse/OEH-68162) — Error|prod|Non-Payables|WP WMS-I-1001 Oracle to SCALE WMS Items Outbound|kIftYlG6EfGRRCGvOXmT4w
	- on review - rejected
- [ ] [OEH-68161](https://warbyparker.atlassian.net/browse/OEH-68161) — Error|prod|Non-Payables|WP GL-I-1060 Payroll to Anaplan|0ZyKB1J-EfG5FrXjBi66GQ
	- on review
- [OEH-68170](https://warbyparker.atlassian.net/browse/OEH-68170) — Error|prod|Non-Payables|IN-I-2017A Fedex Warehouse Transactions Receiving Inbound|abedde12-df50-4051-9e49-05e815ca1398
	- 
- [OEH-68172](https://warbyparker.atlassian.net/browse/OEH-68172) — Error|prod|Non-Payables|WMS-I-1038 Oracle to SCALE WMS Deleted Transfer Orders Out|gcRRUlLeEfGmDlncoSI4Zw
- [OEH-68173](https://warbyparker.atlassian.net/browse/OEH-68173) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|h8wsLlLhEfGwnImYdwL8Rw
- [OEH-68175](https://warbyparker.atlassian.net/browse/OEH-68175) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|GkP0N1LnEfGsSK3kcBpqQA
- [OEH-68176](https://warbyparker.atlassian.net/browse/OEH-68176) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|5PX9KVLpEfGwnImYdwL8Rw
- [OEH-68178](https://warbyparker.atlassian.net/browse/OEH-68178) — Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|F90laFL1EfGsSK3kcBpqQA

## OM-I-3015 – Create EasyPost Adapter to Create and Retrieve Trackers
- tickets:
	- adapter: https://warbyparker.atlassian.net/browse/OTCM-115284
- docs:
	- easypost: https://docs.easypost.com/docs/trackers
	- usps 3.2: https://apis.usps.com/tracking/v3r2
	- usps legacy: https://apis.usps.com/tracking/v3
		- https://developers.usps.com/sites/default/files/apidoc_specs/tracking-v3r2_11.yaml


## AR-I-3019 – Create Integration to Perform Credit Memo Processing
- tickets:
	- integration: https://warbyparker.atlassian.net/browse/OTCM-112853
	- michael: https://warbyparker.atlassian.net/browse/OTCM-108251
- s3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/credit_memos/AR-I-3019/Archive/&showversions=false
- test:
	- see Postman for CURL command
```
Calling lambda API endpoint with OIC creds
$(aws2 configure export-credentials --profile oic --format env)

curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/ar/credit-memo-processing' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"start_date" : "2026-04-01T00:00:00", "end_date": "2026-05-15T00:00:00"}'

curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/ar/credit-memo-processing' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"credit_memo_trx_numbers" : ["CM_Refund_Test1"]}'  -- 300000820155229
```
- notes
	- Credit memo number  e invoice tienen el mismo transaction reference
	- transaction reference es el Sales order creado
	- un Credit memo number  e invoice por transaction reference


## CM-I-3000P - PayPal SFTP Integration and File Sync to S3

- tickets:
	- integration: https://warbyparker.atlassian.net/browse/OTCM-109709
	- oic sched: https://warbyparker.atlassian.net/browse/OTCM-109710
- SFTP access (from Ivan Aguirre)
	- https://github.com/WarbyParker/order-management-gateway/pull/225/changes#diff-942100cadaf12f140d496e256bea7b5788e2b5371de32534279ea603d1c434b4R265-R267
- s3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/external_transactions/CM-I-3005/In/&showversions=false
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/cash_reconciliation/CM-I-3004/In/&showversions=false
- test:
```
Calling lambda API endpoint with OIC creds
$(aws2 configure export-credentials --profile oic --format env)
curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/paypal/sftp-file-sync' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"target_date" : "2026-03-01"}'
```

## AR-I-3019 – Create SOAP Adapter for Credit Memo Refund Transaction Creation

- tickets:
	- https://warbyparker.atlassian.net/browse/OTCM-108230
- oracle soap api:
	- https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/fscmService/CreditMemoService?WSDL
- docs:
	- https://docs.oracle.com/en/cloud/saas/financials/25d/oeswf/receivablescreditmemo-d16509e18469.html#createOnAccountCreditMemoRefund
- test data:
	- Use this query: https://warbyparker.atlassian.net/browse/OTCM-108251

## WMS-I-1006 – Add Source Type Support and SNS Grouping (Ship)

- tickets:
	- https://warbyparker.atlassian.net/browse/OTCM-107354
- s3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2FManhattan%2FWMS-I-1006%2F&region=us-east-1
- query for new relic:
```
SELECT * FROM SpanEvent  where name = 'labs_integrations_transaction_handler' and helios.environment = 'stage'
 SINCE 10 days ago UNTIL now
```

## WMS-I-1020 – Add Source Type Support and SNS Grouping for Wave Release

- tickets:
	- main: https://warbyparker.atlassian.net/browse/OTCM-107351
	- SF global parent: https://warbyparker.atlassian.net/browse/WMS-964
	- OMG global parent: https://warbyparker.atlassian.net/browse/OMG-232
- test data:
	- check: https://warbyparker.atlassian.net/browse/WMS-1029
- s3 files:
	- stage: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2FManhattan%2FWMS-I-1020%2F&region=us-east-1
- expected error on production
	- We **might** encounter old orders that won't have the Source field: Alternatives: 1) fail the whole request (according Miguel, the whole request is needed) 2) Assume that records that don't have the Source field are from SF
		- ![](assets/Pasted%20image%2020260421165005.png)
- FTP error (`SFTP Connection Error: [Errno None] Unable to connect to port 22869 on 172.20.20.144 or 172.20.21.230`)
	- Channel: # lasvegas-wms-implementation
	- ![](assets/Pasted%20image%2020260422084043.png)

## CM-I-3007 - Event Listener and External Transaction Processing
- tickets:
	- https://warbyparker.atlassian.net/browse/OTCM-106697

## Update S3 paths for cash/insurance reconciliation
- tickets:
	- https://warbyparker.atlassian.net/browse/OTCM-106693
- s3 files:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2Fcash_reconciliation%2FCM-I-3004%2F&region=us-east-1

## WMS-I-1005 - pick release line shipment
- tickets:
	- pickrelease adapter: https://warbyparker.atlassian.net/browse/OTCM-105690
	- update integration logic: https://warbyparker.atlassian.net/browse/OTCM-105694
- docs:
	- FSD: https://drive.google.com/file/d/1mbxE4J-vFY6PqVlBJw8J0eqashthZ4FH/
	- API: https://docs.oracle.com/en/cloud/saas/supply-chain-and-manufacturing/25d/fasrp/api-inventory-management-shipment-line-change-requests.html
- oracle erp:
	- oracle get shipment lines from transfer order: see [requests](requests.md)
- s3 files:
	- stage: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?prefix=vendors%2FManhattan%2FWMS-I-1005%2F&region=us-east-1
- logs:
	- `https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights$3FqueryDetail$3D~(end~0~start~-3600~timeType~'RELATIVE~tz~'LOCAL~unit~'seconds~editorString~'fields*20*40timestamp*2c*20*40message*2c*20*40logStream*2c*20*40log*0a*7c*20filter*20*40message*20like*20*2fWMS-I-1005*2f*0a*7c*20sort*20*40timestamp*20desc*0a*7c*20limit*201000~queryId~'adfba303-53c5-4036-95e6-792ef8f02d02~source~(~'*2faws*2flambda*2foic-monocle-integrations-lambda-stage-us-east-1)~lang~'CWLI~logClass~'STANDARD~queryBy~'logGroupName)`


---
## IN-I-2054 - update PO ASNs outbound
- tickets:
	- report+integration: https://warbyparker.atlassian.net/browse/OTCM-105519
- days:
	- [day-20260305](day/day-20260305.md)

---
## CM-I-3004 - payout bank statement import

- tickets:
	- S3 event listener: https://warbyparker.atlassian.net/browse/OTCM-104196
	- integration (upload zip): https://warbyparker.atlassian.net/browse/OTCM-104332
	- bank statement callback: https://warbyparker.atlassian.net/browse/OTCM-105215
- s3:
	- stage: https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors%2Fcash_reconciliation%2FCM-I-3004%2F&tab=objects
- QA steps:
	- Live tail the Cloudwatch logs:
		- /aws/lambda/oic-monocle-integrations-events_handler_lambda-stage-us-east-1
		- /aws/lambda/oic-monocle-integrations-lambda-stage-us-east-1
	- Open OIC instances monitoring for WP Bank Statements Callback Integration:
		- https://design.integration.us-phoenix-1.ocp.oraclecloud.com/?root=monitoringTracking&oj_Router=1N4IgTg9hAuIFzAL6KA&integrationInstance=oictest2-axhxufzsltne-px
	- Then, upload CA-stripe-2026-03-15.zip to https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/cash_reconciliation/CM-I-3004/In/
	- See logs on events_handler_lambda
		- ![](assets/Pasted%20image%2020260325114609.png)
	- Open OIC to see the instance being run.
		- ![](assets/Pasted%20image%2020260325114257.png)
	- See logs on lambda
		- ![](assets/Pasted%20image%2020260325114442.png)
```
/aws/lambda/oic-monocle-integrations-events_handler_lambda-stage-us-east-1
fields @timestamp, @message, @logStream, @log
| filter @message like /CM-I-3004/
| sort @timestamp desc
| limit 1000

/aws/lambda/oic-monocle-integrations-lambda-stage-us-east-1
fields @timestamp, @message, @logStream, @log
| filter @message like /callback/
| sort @timestamp desc
| limit 1000
```
- classes:
	- WpCmI3004PayoutBankStatementFilesListener
- docs:
	- FSD: https://docs.google.com/document/d/1RWzYl3VdoZdHLroiwXv3aiXXo4kWqZ9l
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
- ticket:
	- s3 event listener: https://warbyparker.atlassian.net/browse/OTCM-100904
	- integration (transmit .oma to LMS ftp/queue): https://warbyparker.atlassian.net/browse/OTCM-100905
- S3 files
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/hoya/In/compensated_rx/
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/versant/In/compensated_rx/
- docs:
	- FSD: 
- classes:
	- WpInI2060OMAFileDispatcher

---

## SNS Adapter
- ticket:
	- https://warbyparker.atlassian.net/browse/OTCM-102781
- docs:
	- architecture: https://warbyparker.atlassian.net/wiki/spaces/Argon/pages/9663217730/Tech+Plan+OMG+-+Order+Fulfillment#Proposed-Architecture


---
## MFG-I-3021 - material issue

- ticket
	- timezone: https://warbyparker.atlassian.net/browse/OTCM-105191
	- oic integration: https://warbyparker.atlassian.net/browse/OTCM-94226
	- new integration: https://warbyparker.atlassian.net/browse/OTCM-87918
	- https://warbyparker.atlassian.net/issues/?jql=textfields%20~%20%22MFG-I-3021%22
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
- original tickets: 
	- https://warbyparker.atlassian.net/issues?jql=textfields%20~%20%22MFG-I-3021%22%20AND%20reporter%20!%3D%20633e0a9afedc6169aed9dc30
	- https://github.com/WarbyParker/monocle_integrations/pull/1600
- screens
	- shared by Josué indicating that MFG-I-3021 finished successfully
	- ![](assets/Pasted%20image%2020260317150152.png)

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
