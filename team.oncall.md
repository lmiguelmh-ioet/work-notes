# On-Call OEH

- "Hunter is working on Roosevelt only and should not be tagged in prod issues, @Hunter Governale please disregard"
- status flow
- On call google instructions: 
	- https://docs.google.com/spreadsheets/d/1np28IorbDKbEWFQo-hn-a4TGyz7jqHbSCaT48b66U6k/edit?gid=0#gid=0
	- https://warbyparker.atlassian.net/wiki/spaces/OT/pages/7726531192/Common+Oracle+Integration+On-Call+Issues
	- https://uncovered-harp-6f7.notion.site/Tony-Hands-off-notes-2ed3bf22ce4b807b8842c7d84852d9a2

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
	- https://warbyparker.atlassian.net/jira/software/c/projects/OEH/issues?jql=project%20%3D%20%22OEH%22%20AND%20created%20%3E%3D%20%222026-05-18%22%20AND%20created%20%3C%3D%20%222026-05-25%22%20ORDER%20BY%20created%20DESC
- Gabriel:
	- El objetivo es que tomes ownership de todo lo que salga en el tablero de OEH que este involucrado a nuestra integración
	- Eso no significa que debas arreglar absolutamente todo, hay varios casos que el equipo te puede ayudar y ya sabe como hacerlo

 ## PROMPTS

```
Get me the NOT STARTED tickets for today, yesterday and the day before yesterday. Additionally, add a list of tickets (hiperlinked) each one with its title (sorted from oldest to recent).
-
Get me the NOT STARTED tickets since start of week on Monday. Additionally, add a list of tickets (hiperlinked) each one with its title (sorted from oldest to recent).
---
Regarding OEH-68321:
Find similar issues with similar:
- status: REJECTED/RESOLVED
- title: WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound
- desc: The inventory transaction import process in Oracle has failed
- at least one attachment that contains: Negative inventory balances are not allowed in this organization.
Last 10 tickets.
---
Can you investigate further, try to find the root cause for each problem, and if possible propose a solution
-
For each  ticket, can you investigate further, try to find the root cause for each problem, and if possible propose a solution.
Look up for similar tickets using the tittle and the description that has at least 1 comment. And see who was assigned, if it had comments, anything that give a glimpse of how this was solved. 
For your working and thought proccess, create a directory for it and put it whatever you consider necessary.
Do not execute the solution without user authorization, lay out your plan instead.
- 
Regarding OEH-68225:

Can you investigate further, try to find the root cause for each problem, and if possible propose a solution.

Look up for similar tickets using the tittle and the description ("Errors occurred during ship confirmation processing") and attachment if any ("There are no staged shipment line(s) for the transfer order") that has at least 1 comment. And see who was assigned, if it had comments, anything that give a glimpse of how this was solved.
For your working and thought proccess, create a directory for it and put it whatever you consider necessary.
Do not execute the solution without user authorization, lay out your plan instead.
-
For each  ticket, look up for similar ticket using the tittle and the description. And see who was assigned, if it had comments, anything that give a glimpse of how this was solved.
For your working and thought proccess, create a directory for it and put it whatever you consider necessary.
Do not execute the solution without user authorization, lay out your plan instead.

---
The ticket was reprocessed, can you mark the ticket as REJECTED and add a comment stating it was reprocessed, before applying send me the coment you are going to use. Apply the same process for the 26 remaining tickets with same error "There are no staged lines to process for Transfer Order" from yesterday between 5pm-6pm gmt-5
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
	- https://us-east-1.console.aws.amazon.com/s3/buckets/wp-payroll-to-anaplan-prod?region=us-east-1&prefix=Out/&showversions=false
- retry may succeed (process run at 6AM/6PM)
- comment https://warbyparker.atlassian.net/browse/OEH-68216:
	- File was updated today.
- old tickets:

| Ticket                                                          | Status   | Assignee                            | How it was “solved”                                                                |
| --------------------------------------------------------------- | -------- | ----------------------------------- | ---------------------------------------------------------------------------------- |
| [OEH-68023](https://warbyparker.atlassian.net/browse/OEH-68023) | Rejected | Johnny Coral                        | _“trial balance payroll file was recently updated”_ + screenshot → Rejected May 15 |
| [OEH-67963](https://warbyparker.atlassian.net/browse/OEH-67963) | Rejected | Johnny Coral                        | Same wording + screenshot                                                          |
| [OEH-67854](https://warbyparker.atlassian.net/browse/OEH-67854) | Rejected | Ariel Sperduti                      | _“Closing: trial balance was recently updated today”_ + screenshot                 |
| [OEH-67608](https://warbyparker.atlassian.net/browse/OEH-67608) | Rejected | Emilio → Marcos Hernandez commented | _“Trial Balance payroll file exists in S3”_ + screenshot                           |
| [OEH-67438](https://warbyparker.atlassian.net/browse/OEH-67438) | Rejected | Emilio → Marcos Hernandez           | _“file was uploaded”_ + screenshot                                                 |
| [OEH-65567](https://warbyparker.atlassian.net/browse/OEH-65567) | Rejected | Jerson Morocho                      | _“trial balance was recently updated today”_ (no screenshot)                       |

## WMS-I-1001 Oracle to SCALE WMS Items Outbound

- comment https://warbyparker.atlassian.net/browse/OEH-68217:
	- UPC `9000000000001` is an intended inactive item so it is not synced to SCALE, stated by Alexis here: https://warbyparker.atlassian.net/browse/OEH-67855?focusedCommentId=906458

## IN-I-2017A Fedex Warehouse Transactions Receiving Inbound

### Cases
- received quantities match:
	- https://warbyparker.atlassian.net/browse/OEH-65121
		- Item 10000781: status 'Expected', this is ok — item is not in the FedEx payload, meaning FedEx did not send this item. Received quantity is 0 on both sides.
		- The received quantities in the FedEx payload and Oracle match. No manual intervention required.
	- https://warbyparker.atlassian.net/browse/OEH-65165
		- Item 1158506: status 'Expected', this is ok — item is not in the FedEx payload, meaning FedEx did not send this item. Received quantity is 0 on both sides.
		- Item 1504640 (OPC 846864060589): status 'Partially received', this is ok — FedEx only sends the received quantities. Received quantities in the payload sent by FedEx (3) and Oracle (3) match.
- integration triggered twice:
	- https://warbyparker.atlassian.net/browse/OEH-65344
		- second attempt fails with: Oracle rejected it with `RCV_ASN_SHIPMT_NOT_OPEN`_: "You cannot receive the PO shipment 3 because it is not open.", as it was already received in the first attempt._
- received quantities don't match:
	- https://warbyparker.atlassian.net/browse/OEH-67976
		- reprocessed
	- https://warbyparker.atlassian.net/browse/OEH-67974
		- reprocessed
	- https://warbyparker.atlassian.net/browse/OEH-67981
		- reprocessed
	- https://warbyparker.atlassian.net/browse/OEH-67984
		- reprocessed
- duplicated entry for item
	- https://warbyparker.atlassian.net/browse/OEH-68054
		- reprocessed
- PO closed: Goods Closure Error in Put Away for Transfer Order
	- https://warbyparker.atlassian.net/browse/OEH-66998
	- https://warbyparker.atlassian.net/browse/OEH-65095
- Over-receipt:
	- https://warbyparker.atlassian.net/browse/OEH-58407
- Fully received:
	- https://warbyparker.atlassian.net/browse/OEH-65073
	- https://warbyparker.atlassian.net/browse/OEH-65054
- Header error: "You must enter a transaction quantity that's up to the available quantity of 1"/"There is no quantity to be processed for this transaction"
	- https://warbyparker.atlassian.net/browse/OEH-68329
		- MINE
	- https://warbyparker.atlassian.net/browse/OEH-58563
		- Contacting FedEx Adding @Chelsey Almonte (previouly Danna Williams)
	- https://warbyparker.atlassian.net/browse/OEH-58564
		- Contacting @Chelsey Almonte (previouly Danna Williams)
	- https://warbyparker.atlassian.net/browse/OEH-58569
		- Contacting @Chelsey Almonte (previouly Danna Williams)
	- https://warbyparker.atlassian.net/browse/OEH-58573
		- Contacting @Chelsey Almonte (previouly Danna Williams)

### Instructions
```
For OEH-68312 ticket:

1. create ./tmp/{TICKET} and use it as working directory
2. read the ticket including description
3. fetch inbound shipment lines and save the complete payload `oracle_inboundShipments_{ORDER_NUMBER}.json`: GET /fscmRestApi/resources/11.13.18.05/inboundShipments?finder=findByOrgOrderSupplierShipment;bindTONumber={ORDER_NUMBER}&expand=all
	- e.g. https://fa-evdi-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/inboundShipments?expand=all&finder=findByOrgOrderSupplierShipment%3BbindTONumber%3D1101961
	- run to generate a summary: jq '
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
    }]
  }
'
4. Download FedEx receipt confirm payload from S3 (vendors/OIC-Proxy/IN-I-2017A/Errors/fedex_receipts_receipt_confirm_TO_{SHIPMENT_NUMBER}_???.json)
	- use the wp profile and device-code to login if needed
	- use stdout to communicate with awscli
	- list using the full prefix (not the directory)
	- use the same name for the file in disk
5. Check if ALL lines are 'Fully received' in the inboundShipments file, if true receipt already completed. DONE.
6. If not, make a summary of the lines, status, item numbers and other important information. Include the itemNumbers separated by commas.
7. Wait for the user to give the UPCs and use it to find and compare received quantities per item between FedEx payload and Oracle.
8. Give a final summary like the following:

44/45 inbound lines Fully received; 1 line Expected.
1. Line ERP: `ShipmentLineId` 11099362 / FedEx: `lineNumber` 4:
    - ERP: Item 10001305 - shipped 1, received 0.
    - FedEx: UPC 846864069308 - shipped 0, received 2.

---

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
- in a case reprocessing with (beware there are two integrations with the name 2017As):
	  "WPIN-I-2017A Receipts Fedex Inbound OrchestratorV1 (1.0.1)"
---

CASO Uccuco
2008->2012->2047  
Creacion de PO->Creacion de Shipment-> Receiving

CASO Fedex
pasos anteriores:
1. ? 2017B : pick + ship
2. ?

confirmar en 2 pasos:
- contabilizar: RECEIPT_CONFIRMATION (receipt)
- mover a destino: GOODS_CLOSURE  (put away)

falta: llamar a un reporte para obtener los errores
WP IN Get Errored PO Recepits Report (uses for TOs, SOs, etc)
- purge the tablas interface (por el error de 404)
- reprocesar el registro para obtener el error

- no puedes hacer la recepción si no hay un envío

CASO WMS
en 1 paso: via FBDI

```

![](assets/Pasted%20image%2020260528112837.png)

## WMS-I-1038 Oracle to SCALE WMS Deleted Transfer Orders Out

- review old tickets
- TO CONFIRM: solved automatically every day at 8am / or someone did run a script. This comment was added:

**Status:** ✅ **RECOVERED** — Transient error

| **Failed Instance** | **First Clean Instance (recovery)**               |                                 |
| ------------------- | ------------------------------------------------- | ------------------------------- |
| **Instance ID**     | `gcRRUlLeEfGmDlncoSI4Zw`                          | `6Uc61VLfEfGmDlncoSI4Zw`        |
| **OIC Status**      | COMPLETED (fault handler)                         | COMPLETED (clean)               |
| **Error Stages**    | Transfer_Order_Out Read timed out → Fault Handler | 0 errors (59 stages, all clean) |
| **Timestamp**       | May 18, 17:35 UTC                                 | May 18, 17:45 UTC               |

Integration actively running every ~10 minute. Recovery confirmed on next clean run. No data loss.


## IN-I-2048B Inbound IOT to Oracle ASN

- Review the CSV and check if data is valid

## IN-I-2017B Fedex Warehouse - Pick Ship Confirm Inbound

- Gabriel: 
	- entonces falta el pick confirm en todas ellas
	- Yep todas estan en ready to release
	- bueno de ahí reviso, si recibimos el mensaje de pick para esas ordenes
	- parece que si recibimos :open_mouth:
	- Ya estoy descargando todos los archivos del pick confirm para poder reprocesarlos
	- Confirmado que tenemos todos los pick requests
	- hare un reintento con el primero a ver que tal nos va
	- funcionó sin problemas
	- es solo de reprocesarlos
	- no hay nada que corregir, dame un seg ya envio todos los pick y ship conf, tengo un script para eso
	- solo me falta ajustar un par de cosas
	- me: eso es todo?
	- son los picks, de aqui vienen los ships
	- ahí si los podemos cerrar
- comment https://warbyparker.atlassian.net/browse/OEH-68261:
	- "Transfer Order 1112297 successfully reprocessed."

| Status                | Plain meaning                                                            |
| --------------------- | ------------------------------------------------------------------------ |
| Ready to release      | Oracle knows about the line; warehouse/FedEx flow not really started yet |
| Released to warehouse | Oracle released the line to the warehouse; pick can be recorded          |
| Staged                | Pick confirmed in Oracle; ready for ship confirm                         |
| Interfaced            | Ship confirmed; Oracle considers it fully shipped for this integration   |

Pick confirm = FedEx says “we picked it” → Oracle prepares lines for shipping (Staged).  
Ship confirm = FedEx says “we shipped it” → Oracle closes the shipment (Interfaced).  
Ship cannot run before pick (and staging) succeeds.

## WMS-I-1041 Breakage Notification from LMS to Springfield

### File located at '...' could not be moved to '...'.

- check if file is already on Archive:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-prod-data?region=us-east-1&prefix=vendors%2Finnovations_lms%2FArchive%2FLLAS%2F20260519%2F&showversions=false&tab=objects
- confirm there was a second try that failed:
	- `https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#logsV2:logs-insights$3FqueryDetail$3D~(end~'2026-05-20T04*3a59*3a59.000Z~start~'2026-05-19T05*3a00*3a00.000Z~timeType~'ABSOLUTE~tz~'LOCAL~editorString~'fields*20*40timestamp*2c*20*40message*2c*20*40logStream*2c*20*40log*0a*7c*20filter*20*40message*20like*20*2fAttempting*20to*20move*20file*20from*20*27vendors*5c*2finnovations_lms*5c*2fOut*5c*2fLLAS*5c*2fLV3K3N2Q5-LV3K3N2Q5-1.RXT*27*2f*0a*7c*20sort*20*40timestamp*20desc*0a*7c*20limit*201000~queryId~'46175e02-b93a-4886-9d32-da2f3e50996c~source~(~'*2faws*2flambda*2foic-monocle-integrations-events_handler_lambda-prod-us-east-1~'*2faws*2flambda*2foic-monocle-integrations-lambda-prod-us-east-1)~lang~'CWLI~logClass~'STANDARD~queryBy~'logGroupName)`
- comment from https://warbyparker.atlassian.net/browse/OEH-68209:
	- "This is the second try. First try was successful."

## WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound

### Negative inventory

- NOTE: this is related to NEGATIVE inventory
- TO CONFIRM: solved automatically every day at 8am / or someone did run a script. This comment was added:

Andrew’s team will handle the transactions with the negative inventory balances error [as part of the monthly close process](https://warbyparker.atlassian.net/browse/OEH-33303?focusedCommentId=801660). Therefore, this ticket can be marked as REJECTED.
### Invalid product code

- check: https://warbyparker.atlassian.net/browse/OEH-68201
- - Invalid product code — no product identifier found in Oracle
- notify andrew
- message:
```
- **Error:** Invalid product code — no product identifier found in Oracle
    
- **UPC/OPC:** `846864059019`
    
- **Warehouse:** LLAS
  
Similar to [OEH-67327: Error|prod|Non-Payables|WP WMS-I-1009 SCALE WMS to Oracle Inv Transactions Inbound|2ec35a96-fec3-44a3-85e4-c84f651a8d1dRejected](https://warbyparker.atlassian.net/browse/OEH-67327) :  
  
@Andrew Galloway @Alexis Tomacruz, could you please confirm whether that product code has already been updated in Oracle? If so, could you share the new value so we can manually update the WMS file we received and reprocess only the transaction involved in this incident?
```

## Oracle ERP to Coupa COA Integration

JQL used: `project = OEH AND summary ~ "Coupa COA"` (15 hits; filtered to those with comments).

|Ticket|Status|Assignee|How it was solved|
|---|---|---|---|
|[OEH-67733](https://warbyparker.atlassian.net/browse/OEH-67733) (May 6)|Rejected|Tony Huang|Same CSV pattern (4 malls). Tony: _“AP confirm these facilities are present on coupa, we can close out”_|
|[OEH-67293](https://warbyparker.atlassian.net/browse/OEH-67293)|Resolved|Marcos Hernandez|@Sean Jung — facilities listed; Sean: all exist in Coupa|
|[OEH-65625](https://warbyparker.atlassian.net/browse/OEH-65625)|Resolved|Miguel Munoz|Same loop with Sean Jung|
|[OEH-65057](https://warbyparker.atlassian.net/browse/OEH-65057)|Resolved|Josue Cando|Sean: facilities already exist|
|[OEH-62428](https://warbyparker.atlassian.net/browse/OEH-62428)|Rejected|Marcos Hernandez|_“These facilities exist in Coup…”_ — close for that reason|
|[OEH-62292](https://warbyparker.atlassian.net/browse/OEH-62292)|Resolved|Miguel Munoz|Exception: naming ambiguity (Union Square CA vs NY) — not a simple “already exists”|
- message https://warbyparker.atlassian.net/browse/OEH-68218:
```
Hi @Sean Jung ! Could you kindly help us check if the following facilities were created in Coupa? Thanks in advance for your help  

`Cary Court Liberty Center Orchard Town Center Woodbury Lakes`

cc: @Tony Huang
```

## WMS-I-1006 Ship Confirmation from WMS to Oracle/Springfield/LMS

- ?

## WMS-I-1005 failed or not called (happens!)

- s3
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-prod-data?region=us-east-1&prefix=vendors/Manhattan/WMS-I-1005/&showversions=false
- lookup in cloudwatch logs:
- `monocle_integrations/_api/_routes/_pick_ship_confirm/_scale_wms_pick_confirmation_routes.py`
```
WMS-I-1005
Transfer Orders: 1, Sales Orders (ERP pick required): 0, Sales Orders (fulfillment only): 0
Processing pick confirmation for order number: 1112364
Oracle Reader - Requested shipment lines for order '1112364' with OrderTypeCode='TRANSFER_ORDER'
...
Successfully processed pick confirmation for order: 1112364
...
File created: scale_pick_conf_05212026170402_8590b819-8d23-4e97-abcf-f1839753fbe8.json in vendors/Manhattan/WMS-I-1005/Archive/05212026
```
- message https://warbyparker.atlassian.net/browse/OEH-65462
	- ask for payload


## IN-I-2043 Case Optics To Oracle ASN - Inbound

- S3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/transfer-prod-data?region=us-east-1&prefix=vendors/case_optics/In/&showversions=false
- Purchase orders:
	- Home > Procurement > Purcharse Orders: Search icon, choose Orders, write PO3180

### PO line number is missing
- old tickets

| Ticket                                                          | Integration        | Assignee         | Resolution pattern                                                                  |
| --------------------------------------------------------------- | ------------------ | ---------------- | ----------------------------------------------------------------------------------- |
| [OEH-67070](https://warbyparker.atlassian.net/browse/OEH-67070) | IN-I-2043          | Miguel Munoz     | Same error for `PO3131`; reprocessed → “ASN reprocessed successfully”               |
| [OEH-67033](https://warbyparker.atlassian.net/browse/OEH-67033) | IN-I-2043          | Miguel Munoz     | Shipment reprocessed successfully                                                   |
| [OEH-65325](https://warbyparker.atlassian.net/browse/OEH-65325) | IN-I-2043          | Johnny Coral     | “Reprocessed and shipment created” → Rejected                                       |
| [OEH-54380](https://warbyparker.atlassian.net/browse/OEH-54380) | IN-I-2043          | Jerson Morocho   | Re-ran with file → ASN created                                                      |
| [OEH-67191](https://warbyparker.atlassian.net/browse/OEH-67191) | (missing shipment) | Alexis Tomacruz  | ASN file reprocessed                                                                |
| [OEH-18357](https://warbyparker.atlassian.net/browse/OEH-18357) | IN-I-2043          | —                | Diego Pardo: line missing at first run; later run fully shipped → close as expected |
| [OEH-14999](https://warbyparker.atlassian.net/browse/OEH-14999) | IN-I-2043          | —                | Kaio Amaral: “PO line number missing, this is normal behavior”                      |
| [OEH-64911](https://warbyparker.atlassian.net/browse/OEH-64911) | IN-I-2043          | Marcos Hernandez | Rejected — PO already fully shipped                                                 |
| [OEH-61505](https://warbyparker.atlassian.net/browse/OEH-61505) | IN-I-2048 (SOMO)   | Emilio Lopez     | Different integration; PO re-processed after fix elsewhere                          |
- steps
	- copy the file from error to In
	- run the OIC integration
	- wait ~10 minutes, 
	- ERP: In purchase order, View Details, shipped should be moving in quantity until reach the same height as ordered, invoiced
- message https://warbyparker.atlassian.net/browse/OEH-68263:
	- Attempting to re-process using this file: ...


## WMS-I-1031 Production Status Updates from LMS to WMS/Springfield

- Check if file is in Archive, JUST REPLACE Out FOR Archive AND VERIFY IF EXIST (DO NOT ADD 20260521 IN THE PATH!!!)
- S3:
	- 
- https://warbyparker.atlassian.net/browse/OEH-68273
	- Duplicate S3 event (NoSuchKey). File already processed and present under `vendors/innovations_lms/Archive/`.

## IN-I-2055 Oracle ERP to Fedex TO Outbound

- see excel
- "This is a transient error that occurs when calling the report. This integration run every 10 minutes. A sequential run was successful so no further action is required."

## WMS-I-1003 Oracle to SCALE WMS Inbound TO ASNs

- see excel
- "This is a transient error that occurs when calling the report. This integration run every 10 minutes. A sequential run was successful so no further action is required."

## ERP to Anaplan PO Sync

- S3:
	- https://us-east-1.console.aws.amazon.com/s3/buckets/wp-oracle-anaplan-datahub-prod?region=us-east-1&prefix=Out/&showversions=false
- 