- point to dev1/evdi-test
	- https://github.com/WarbyParker/monocle_integrations/pull/1700/changes
- circle ci
	- https://app.circleci.com/pipelines/github/WarbyParker/monocle_integrations
- create adapter
	- [team](team.md)
- create pr:
	- [team](team.md)
- each one of these projects must have a CURL to the Oracle 

"Ser padre me ha enseñado que existe un nuevo sentido a la vida.
Que entre momentos dulces y salados, uno encuentra dicha y felicidad."



## ON-CALL: JUL6-JUL12
- https://warbyparker.atlassian.net/jira/software/c/projects/OEH/list?jql=project%20%3D%20%22OEH%22%0AAND%20created%20%3E%3D%20%222026-07-06%22%0AAND%20created%20%3C%3D%20%222026-07-13%22%0AAND%20status%20NOT%20IN%20(Rejected%2C%20Resolved)%0AORDER%20BY%20created%20DESC
- self-heal maybe?
	- https://warbyparker.atlassian.net/browse/OEH-69691

## FLARE to OIC: Ship Confirmation (AI SRW)
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-118998
- s3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-stage-data?region=us-east-1&prefix=vendors/OIC-Proxy/IN-I-2017B/Archive/&showversions=false
	- https://us-east-1.console.aws.amazon.com/s3/object/transfer-stage-data?region=us-east-1&prefix=vendors/OIC-Proxy/IN-I-2017B/Archive/fedex_ship_conf_TO_1123866_07072026214943_v2G9LnpNEfGCVXfkx3ah-g.json
- docs:
	- https://docs.google.com/document/d/1LRj62d2Dr8EMAyL275a3F4wCJlFQ58_f/edit
	- https://docs.google.com/document/d/1aV-YWDpvOCI7EvY5_e27J0iurPMAC5sT/edit
- notes
```
- SCAC = Standard Carrier Alpha Code — identifies the carrier (who ships it). Examples from this file: `UPS`, `FDEG` (FedEx Ground), `UPSW`, `BGLF`.
- SCSC = Standard Carrier Service Code — identifies the service level / ship method (how it ships). Examples: `GND`, `2DA`, `NDA`, `FEDEX_GROUND`.
```
## RMCS-I-3001 Create monocle-app domain integration
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-129762
- test
```
data: https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/analytics/saw.dll?bipublisherEntry&Action=open&itemType=.xdo&bipPath=%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo&path=%2Fshared%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo

Calling lambda API endpoint with OIC creds
$(aws configure export-credentials --profile oic --format env)
$(aws configure export-credentials --profile ott --format env)

# OTT
curl -v -X POST 'https://bocjed6ra6ycbe2wampw2idkiq0hihsg.lambda-url.us-east-1.on.aws/rmcs/proof-of-delivery-upload' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"sales_order_numbers" : ["19"]}' -H "OIC-Instance-ID: 1"

# STAGE
curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/rmcs/proof-of-delivery-upload' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"sales_order_numbers" : ["19"]}' -H "OIC-Instance-ID: 1"
```

## RMCS-I-3001 Create monocle-app Customer Contract Source Data Import FBDI
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-129760

## RMCS-I-3001 Create BIP report to retrieve deliver and shipped date of SOs
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-129759

## RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach
- query
[projects.RMCS-I-3001](projects.RMCS-I-3001.md)

- info
```
Proof of Delivery upload (RMCS-I-3001) → Import Revenue Basis Data

1. POD is an additional satisfaction event on `VRM_SOURCE_DOC_ADDL_SUBLINES` [https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/guidelines-for-importing-additional-satisfaction-events.html](https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/guidelines-for-importing-additional-satisfaction-events.html)
    
2. That sheet belongs to `RevenueDataImportTemplate.xlsm`; scheduled process is Import Revenue Basis Data [https://docs.oracle.com/en/cloud/saas/financials/26b/oefbf/revenuebasisdataimport-3195.html](https://docs.oracle.com/en/cloud/saas/financials/26b/oefbf/revenuebasisdataimport-3195.html)
    
3. Manual load steps: "Select Import Revenue Basis Data as the import process" [https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/how-revenue-basis-import-data-is-processed.html](https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/how-revenue-basis-import-data-is-processed.html)
    
4. Billing is a different process (for contrast) [https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/how-billing-data-import-data-is-processed.html](https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/how-billing-data-import-data-is-processed.html) [https://docs.oracle.com/en/cloud/saas/financials/26b/oefbf/billingdataimport-3228.html](https://docs.oracle.com/en/cloud/saas/financials/26b/oefbf/billingdataimport-3228.html)
    
5. Warby internal spec (section 1.2) `docs/RMCS-I-3001/RMCS-I-3001 - Proof of delivery upload in RMCS - FBDI Approach.docx.md`
    
6. Stage pod confirmation — ESS job `111610505`, argument1 = `54`, Import Process = Import Revenue Basis Data

---

|[Revenue Basis Data Import (FBDI catalog)](https://docs.oracle.com/en/cloud/saas/financials/26b/oefbf/revenuebasisdataimport-3195.html)|UCM account: `fin/revenueManagement/import`|
|[How Revenue Basis Import Data Is Processed](https://docs.oracle.com/en/cloud/saas/financials/26b/fafrm/how-revenue-basis-import-data-is-processed.html)|_"Select fin/revenueManagement/import as the account"_ in File Import and Export|
|[ERP Integrations REST API](https://docs.oracle.com/en/cloud/saas/financials/26b/farfa/op-erpintegrations-post.html)|`DocumentAccount` format with `$` escaping|

```
- CURSOR REQUEST ID: bcfca2bf-e172-41a0-bc62-89cc14a53c1f
```
RMCS stands for Revenue Management Cloud Service. It is an Oracle Fusion Cloud ERP module whose job is to decide when and how much revenue a company can recognize, according to accounting rules (especially ASC 606 / IFRS 15).
1. A B2C sales order is created on 05/29/2026.
2. Items ship on 06/03/2026.
3. The customer actually receives them on 06/05/2026.

OM: What did the customer order, ship, and receive?
AR: What do we bill and collect?
RMCS: When can we count that sale as revenue in the books?

OM knows about the order and shipment. RMCS needs to know that delivery happened before it can treat the revenue obligation as satisfied.
That is exactly what RMCS-I-3001 does: upload **Proof of Delivery** (POD) into RMCS so revenue can be recognized at the right time.

   Customer places order
        ↓
   Order Management (OM)     ← operational truth: order, ship, deliver
        ↓
   Revenue Management (RMCS) ← accounting truth: when revenue is earned
        ↓
   General Ledger (GL)       ← financial postings

Flow:
1. A sales order line is shipped and delivered in OM
2. Delivery date is stored on the shipment line (from EasyPost, in Warby’s case)
3. Integration finds new/changed delivered lines since last run
4. Integration maps OM/RMCS IDs into FBDI sheet 4
5. FBDI file is uploaded to Oracle Fusion
6. RMCS validates against existing contract lines
7. If valid → satisfaction event recorded → revenue recognition can proceed
8. If invalid → errors appear in “Correct Contract Document Errors in Spreadsheet”

|Document type|Module|Typical purpose|Relation to RMCS tickets|
|---|---|---|---|
|Sales order|OM|Customer buys product|3001 (fulfillment/POD), 3003 (order details)|
|RMA / return order|OM|Customer returns product|3003 (order details), not POD|
|AR invoice|AR|Bill the customer|3002 (billing lines)|
|AR credit memo|AR|Reverse/adjust billing|3002|
|Transfer order|OM/INV|Move stock between warehouses|Not in these RMCS tickets|
|Purchase order|Procurement|Buy from supplier|Not in these RMCS tickets|
|Work order|Manufacturing|Build/assemble items|Not in these RMCS tickets|

3003 → What was sold or returned? (master order data → RMCS contract/source doc)
3001 → Was the sale fulfilled? (POD → satisfaction event → earn revenue)
3002 → What was billed/credited? (AR invoice / credit memo → billing side)

> 3001 records proof that we delivered on a sales order so RMCS can recognize revenue.  
> 3003 supplies order and RMA master data so RMCS can create the contract/source document in the first place.  
> 3002 handles the billing and credit side in AR.  
> Returns are not negative POD; they are separate documents and events (3003 + 3002).

why not one report?
1. Different triggers — contract creation (3003) vs delivery date change (3001) vs invoice posted (3002).
2. Different RMCS FBDI targets — source documents vs additional satisfaction events vs billing lines.
3. RMA in 3003 only — product owners already split the domain.
4. POD is meaningless for RMA — returns use return/receipt/credit semantics, not “proof of delivery to customer.”
```
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-129759
	- 
- related tickets from others
	- 3002: https://warbyparker.atlassian.net/browse/OTCM-129764
	- 3003: https://warbyparker.atlassian.net/browse/OTCM-129771
```
RMCS-I-3001
“When was it shipped/delivered?” → feeds POD / fulfillment events in RMCS
RMCS-I-3003
“What was sold or returned?” → feeds contract / source document creation in RMCS
RMCS-I-3002
“What was billed or credited?” → feeds AR billing events in RMCS
```
- docs
	- FSD: https://docs.google.com/document/d/1BZInnIPHh0s6zG6n6Q6I93yGBVjl28Z8/edit
	- FSD mapping: https://docs.google.com/spreadsheets/d/1ZTlE9RFYYRHej9ZPCi3zxAwbA0hv9MoF/edit?gid=470165428#gid=470165428
	- FBDI sheet: https://docs.google.com/spreadsheets/d/19e-Ga-ryrvCWIXhlQ4JdYJaeDIcrCCik/edit?gid=2037721153#gid=2037721153
- test:
```
El reporte se encuentra en:  

- https://fa-evdi-dev1-saasfaprod1.fa.ocs.oraclecloud.com/analytics/saw.dll?bipublisherEntry&Action=open&itemType=.xdo&bipPath=%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo&path=%2Fshared%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo
  
- https://fa-evdi-test-saasfaprod1.fa.ocs.oraclecloud.com/analytics/saw.dll?bipublisherEntry&Action=open&itemType=.xdo&bipPath=%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo&path=%2Fshared%2FCustom%2FWP%20Integrations%2FFIN%2FWP%20RMCS%20Order%20Details%20Additional%20Sub%20Lines%20Report.xdo
```
## OM-I-3015 – Create Scheduled Sync for Tracking Numbers with EasyPost
- TODO: CREATE THE API KEY WE ARE GOING TO USE IN PROD
- tickets:
	- initial monolith: https://warbyparker.atlassian.net/browse/OTCM-120426
	- sqs: https://warbyparker.atlassian.net/browse/OTCM-125481
	- enqueue process: https://warbyparker.atlassian.net/browse/OTCM-125483
- test
```
$(aws configure export-credentials --profile oic --format env)

curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/easypost/tracker/sync' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H "OIC-Instance-ID: 1"
```

```
$(aws configure export-credentials --profile oic --format env)

python scripts_local/seed_tracking_references_stage.py --confirm stage --pending 1 --enqueued 0 --created 0 --failed 0 --skipped 0 --table oic-monocle-integrations-stage-tracking-references --single-write

```
- logs
```
fields @timestamp, @message, @logStream, @log
| filter @message like /OM-I-3015/
| sort @timestamp desc
| limit 1000
```

## AP-I-3006 – Create Report and Monocle Reader for Refund Information

- query:
	- [projects.AP-I-3006](projects.AP-I-3006.md)
- tickets:
	- https://warbyparker.atlassian.net/browse/OTCM-117265


## WMS-I-1005 – Update Pick Slip Confirmation Adapter to Send Short Pick Reason Only When Applicable
- tickets
	- https://warbyparker.atlassian.net/browse/OTCM-119708


## ON-CALL: MAY18-MAY25
- https://warbyparker.atlassian.net/jira/software/c/projects/OEH/issues?jql=project%20%3D%20%22OEH%22%20AND%20created%20%3E%3D%20%222026-05-18%22%20AND%20created%20%3C%3D%20%222026-05-25%22%20ORDER%20BY%20created%20DESC
- 2 tickets on hold

## OM-I-3015 – Create EasyPost Adapter to Create and Retrieve Trackers
- tickets:
	- adapter: https://warbyparker.atlassian.net/browse/OTCM-115284
- docs:
	- joshua&luis abrie: 
		- [day-20260508](day/day-20260508.md)
	- easypost: 
		- https://docs.easypost.com/docs/trackers
		- https://docs.easypost.com/guides/tracking-guide
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
$(aws configure export-credentials --profile oic --format env)

curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/ar/credit-memo-processing' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"start_date" : "2026-04-01T00:00:00", "end_date": "2026-05-15T00:00:00"}'

curl -v -X POST 'https://sjlqdgbb5mesmduz4pw5oj6fsa0ykkxk.lambda-url.us-east-1.on.aws/ar/credit-memo-processing' -H "x-amz-security-token: ${AWS_SESSION_TOKEN}" --aws-sigv4 "aws:amz:us-east-1:lambda" --user "${AWS_ACCESS_KEY_ID}:${AWS_SECRET_ACCESS_KEY}" -H 'Content-Type: application/json' -d '{"credit_memo_trx_numbers" : ["1001"]}'  -- 1001 / 300000820155229 / CM_Refund_Test1
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
