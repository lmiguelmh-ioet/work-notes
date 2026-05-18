# On-Call OEH

- On call google sheet instructions: 
	- https://docs.google.com/spreadsheets/d/1np28IorbDKbEWFQo-hn-a4TGyz7jqHbSCaT48b66U6k/edit?gid=0#gid=0

- Github tree with Ariel scripts:
	- https://github.com/WarbyParker/monocle_integrations/pull/1924
    - [1009_negative_inventory_check.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-ce6f41c1ed8f5e9ff5784fac9a2058fa2b840b30e489073f8176b8ce30ee8c8e)
    - [1026_quantity_exceeds_check.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-458e793967b7cc4f516aab2082996d218d0885ccfd4436b9994923798bcae38d)
    - [1031_event_duplicate.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-91fce8276a354685514d3c9c2b138347cb3ec4b5a1d3d4fc1a24ac3c30ffd229)
    - [1031_event_reprocess.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-278afd40dac1f41fb48cab99304f1a714a71c6397b1d6f4ed44a513c589a0eab)
    - [1031_reject_jira_trayid.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-f0cda7e450c93666b707d4342421093be4d75fac9da1699425f985ed7a76a0f1)
    - [1031_reject_test_order_errors.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-905bc902771d1c128a3b4b9f58ded8ad7d2120e284bd04fa6cbb0a64721ab795)
    - [2022_reject_errors.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-dfb14d9558450d00c570e9cd132c7fd7dbd2d42a6e85b79962c24385e0cc024e)
    - [transfer_order_receipt_confirm_processor.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-308726977b312e1d022e54f3d235d79404d767d76ff5512e54f81ec195abba2c)
    - [transfer_order_ship_confirm_processor.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-8a08e00a2d0240b66b76850f4c9e63d66a99cafd336371c417cef722cdc83ded)
	- [orchestrator.py](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-9b08ef56c7212984e66fb0ada4a36cfe59605d993fe90373460159b26684d648)
	- [requirements.txt](https://github.com/WarbyParker/monocle_integrations/pull/1924/changes#diff-b32ddb06b837eb697127ce0b69423d11b51c23f78eebfde2b4c089663de06e78)

- Github tree with agent data:
	- https://github.com/WarbyParker/monocle_integrations/tree/on-call-agent
- Tablero OEH:
	- https://warbyparker.atlassian.net/jira/software/c/projects/OEH/issues?jql=project%20%3D%20%22OEH%22%20ORDER%20BY%20created%20DESC
- Gabriel:
	- El objetivo es que tomes ownership de todo lo que salga en el tablero de OEH que este involucrado a nuestra integración
	- Eso no significa que debas arreglar absolutamente todo, hay varios casos que el equipo te puede ayudar y ya sabe como hacerlo
- Prompts inside the on-call-agent:

```
Get me the NOT STARTED tickets for today. Additionally, add a list of tickets (hiperlinked) each one with its title (sorted from oldest to recent).
---
only for not started one, can you investigate further, try to find the root cause for each problem, and if possible propose a solution
---
for each one, give me who will be the possible owner? e.g. the main author or the one who has more lines modified in git
---
From:
@chat-id
Look up similar ticket for OEH-68165 (using the tittle and the description with text: "Error receiving order number: XXX and shipment number: XXX.").
And see who was assigned, if it had comments, anything that give a glimpse of how this was solved.
---
From: chat
 
Try to solve: OEH-68170

Step 1 is to fetch inbound shipment lines: GET /fscmRestApi/resources/11.13.18.05/inboundShipments?finder=findByOrgOrderSupplierShipment;bindTONumber={ORDER_NUMBER}&expand=all

see @on-call-agent/skills/erp-skill/SKILL.md

```


## GL-I-1060 Payroll to Anaplan

- file should exist on S3 
	- https://us-east-1.console.aws.amazon.com/s3/buckets/wp-payroll-to-anaplan-prod?region=us-east-1&prefix=Archive/&showversions=false
- retry may succeed (process run at 6AM/6PM)

## WMS-I-1001 Oracle to SCALE WMS Items Outbound

- UPC `9000000000001` is an intended inactive item so it is not synced to SCALE, stated by Alexis here: https://warbyparker.atlassian.net/browse/OEH-67855?focusedCommentId=906458

## IN-I-2017A Fedex Warehouse Transactions Receiving Inbound

```
Check inbound shipment line statuses in Oracle:  
1. Fetch inbound shipment lines: GET /fscmRestApi/resources/11.13.18.05/inboundShipments?finder=findByOrgOrderSupplierShipment;bindTONumber={ORDER_NUMBER}&expand=all

curl --location 'https://fa-evdi-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/inboundShipments?expand=all&finder=findByOrgOrderSupplierShipment%3BbindTONumber%3D1101961' \
--header 'REST-Framework-Version: 3' \
--header "Authorization: Basic $ERP_BASIC_AUTH"

jq '
  .items[] | {
    ShipmentNumber,
    ShipmentHeaderId,
    ReceiptNumber,
    HeaderInterfaceId,
    TransferOrderNumber: (.shipmentLines.items[0].TransferOrderNumber // null),
    line_count: (.shipmentLines.items | length),
    all_fully_received: ([.shipmentLines.items[].ShipmentLineStatusCode] | all(. == "FULLY RECEIVED")),
    not_fully_received: [.shipmentLines.items[] | select(.ShipmentLineStatusCode != "FULLY RECEIVED") | {
      ShipmentLineId,
      ItemNumber,
      ShipmentLineStatus,
      ShipmentLineStatusCode,
      QuantityShipped,
      QuantityReceived,
      qty_remaining: (.QuantityShipped - .QuantityReceived)
    }],
    failed_line_from_ticket: [.shipmentLines.items[] | select(.ShipmentLineId == 11085765) | {
      ShipmentLineId,
      ItemNumber,
      ShipmentLineStatus,
      ShipmentLineStatusCode,
      QuantityShipped,
      QuantityReceived,
      qty_remaining: (.QuantityShipped - .QuantityReceived)
    }]
  }
' tmp/json3.json > tmp/json3-summary.json
2. If ALL lines are 'Fully received' → reject the ticket (receipt already completed)  
3. If NOT all lines are fully received → download FedEx receipt confirm payload from S3 (vendors/OIC-Proxy/IN-I-2017A/Errors/fedex_receipts_receipt_confirm_TO_{SHIPMENT_NUMBER}_???.json)  
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-prod-data?region=us-east-1&prefix=vendors/OIC-Proxy/IN-I-2017A/Errors/&showversions=false   
4. Resolve item identifiers (FedEx uses OPC, Oracle uses ItemNumber) via Oracle BI report: Shared Folders/Custom/WP Integrations/SCM/WP GET ITEMS BY IDENTIFIERS
5. Compare received quantities per item between FedEx payload and Oracle
6. If quantities match → reject with a detailed line-by-line comment  
7. If quantities mismatch → ticket needs manual attention
```