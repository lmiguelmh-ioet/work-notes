> ARCHIVED 2026-10-06 — frozen. RICE-level notes are superseded by per-ticket
> files (see [README](README.md) → "Project notes (ticket-scoped)"); operational
> knowledge lives in skills (`rmcs-test-data`, `om-order-lifecycle`). Kept for
> the query collection and the 2026-09 spike logs. The PR-series section below
> is STALE — current status: [projects.RMCS-I-3001.OTCM-139313](projects.RMCS-I-3001.OTCM-139313.md).

## PR series (OTCM-139313) — status 2026-09-29

- monocle **#2587** (PoD reader adapter) — merged.
- monocle **#2589** (port models + `ProofOfDeliveryImportModelsMapper`) — open; review
  resolved: `contract_end_date` now required on both port models (reader + import action),
  so a dateless "U" update is unrepresentable (the adapter already fails loud on blank
  `CONTRACT_END_DATE`).
- oracle-integration-cloud **#1102** (warranty branch on the order-details DM) and
  **#1105** (`WP_RMCS_PROOF_OF_DELIVERY_DM`) — open.
- Open design point: U-record optional-vs-required field shape is pending Aruna's
  confirmation; until then the model honors the mapping sheet (restated Required fields,
  `contract_line_type` optional). Any trim lands before the writer PR.
- Next: activation PR — wire the mapper, extend `init_import_models` so
  `source_doc_line_updates` reach the FBDI payload, add the VRM_SOURCE_DOC_LINES
  control-file layout to the writer.

## Test data generator (PoD report)

- Deferred: **warranty branch** test data (order 274/275 have WP_AI_WARRANTY lines with item
  49000007, commission DFF exists; needs RMCS split config verified so the contract produces
  .1/.2/.3 split lines). Regular branch first.
- Deferred: **stage-Lambda path** for the RMCS contract load (`POST /rmcs/contract-creation`,
  stage config points at dev1 Oracle). For now the load is manual: FBDI `VrmRblImport.dat`
  via `importBulkData` (VRMPRCBL, interface 54, account `fin$/revenueManagement$/import$`)
  + `IdentifyContractObligation` ESS job.
- Naming: `TestPoD<N>` source order numbers.

### Order creation spike (dev1, 2026-09-28) — verified facts

- REST order entry is blocked for the integration user (salesOrders/draftOrders/orderCaptures → 404).
  Working path: **SOAP `OrderImportService`** at `$ERP_BASE_URL/fscmService/OrderImportService`,
  operation `createOrders` (sync), SOAPAction `.../orderImportService/createOrders`.
  Wrapper: `types:createOrders` → `types:request` (type `OrderImportRequest`) → `BatchName` + `Order`.
- Order type is set explicitly via header `TransactionTypeCode` (e.g. `WP_B2C`); line type via
  line `TransactionLineTypeCode` (order 274 line 1 uses `WP_B2C` as line type too).
  Existing orders use `SourceTransactionSystem` = `OPS` (numeric orders) or `OMG` (Test* orders).
- Submit immediately: `OrderPreferences/SubmitFlag = true`.
- Quantities/prices are ADF types: `OrderedQuantity` = MeasureType (`unitCode` attr, e.g. `EA`),
  `UnitSellingPrice` = AmountType (`currencyCode` attr).
- EFF payload shape: header `AdditionalHeaderInformationCategories` with
  `xsi:type="…flex/headerCategories/j_HeaderEffDooHeadersAddInfoprivate"`, `Category=DOO_HEADERS_ADD_INFO`,
  then context element `HeaderEffBRevenue_5FManagement_5FInformation_5FHeaderprivateVO`
  (children `channel`, `allocationFlag` in `…/flex/headerContextsB/` ns).
  Line equivalent: `AdditionalFulfillmentLineInformationCategories`,
  `xsi:type="…flex/fulfillLineCategories/j_FulfillLineEffDooFulfillLinesAddInfoprivate"`,
  `Category=DOO_FULFILL_LINES_ADD_INFO`, context
  `FulfillLineEffBRevenue_5FManagement_5FInformation_5FLineprivateVO`
  (`costCenter`, `productSegment`, … in `…/flex/fulfillLineContextsB/` ns).
  Other line contexts available: `Warranty`, `LmsDetails`, `PrescriptionDetails`,
  `OverrideRevenueManagementInteg` (`suppressSendToRmcs`).
- Clone source = order `274` (WP_B2C, B2C Customer):
  - Customer `B2C Customer`: party_id 300000876780446, party_number 257035.
  - Bill-to: cust_acct_id 300000876780448, site_use 300000876780452.
    Ship-to: party_site_id 300000876780450 (from `DOO_ORDER_ADDRESSES`, keyed by
    header_id + ADDRESS_USE_TYPE; doo_headers_all has NO ship-to/bill-to columns).
  - Header EFF `Revenue_Management_Information_Header`: channel=`1901`, allocationFlag=NULL.
  - Fulfill line EFF `Revenue_Management_Information_Line`: costCenter=`3FED`,
    productSegment=`1301` (line 1) / `1302` (warranty line); `Override_…_Integration`: char2=`No`.
  - EFF storage: `DOO_HEADERS_EFF_B` / `DOO_FULFILL_LINES_EFF_B` (context_code + attribute_charN).
  - Line 1: item `19000009` (= inventory_item_id 100000146800120), UOM `EA`, price 375.
- Fulfill org: orders 274/275 shipped item 19000009 from org `300000020186796`.
  `inv_onhand_quantities_detail` shows ZERO rows for that whole org (BIP-visible view), yet 735
  lines shipped from it in the last 10 days → fulfillment works there regardless; item also has
  503 on-hand in org `300000020186911` (Active) as fallback.
- BU: `RequestingBusinessUnitIdentifier` 300000004163174 (Warby Parker US); currency USD; channel WWW.
- Column gotchas (BIP-exposed names): `doo_lines_all` has INVENTORY_ITEM_ID (no ITEM_NUMBER),
  no ORDERED_QUANTITY (that's on fulfill lines); `doo_fulfill_lines_all.INVENTORY_ORGANIZATION_ID`
  (no WAREHOUSE_ID); EFF tables are `*_EFF_B` (no `*_ADD_INFO`).

### SOAP createOrders dead end → REST salesOrdersForOrderHub (2026-09-28)

- SOAP `createOrders` validated field-by-field (errors: missing SourceTransactionScheduleIdentifier,
  then CATEGORY_CODE → line `TransactionCategoryCode=ORDER`), then stalled on a generic
  "This error occurs in source order …, on source order line 1, source item name …" wrapper with
  NO detail message (checked `DOO_MESSAGES_B`+`_TL` — only the wrapper is logged; EFF/price/date
  bisection all failed identically). Abandoned after 8 iterations.
- EFF gotcha in SOAP: `Category` inside `Additional*InformationCategories` must be in the
  `…/doo/processOrder/model/` namespace (base type), not the service namespace — otherwise it is
  silently dropped and the call fails with "property index out of range".
- **Validation errors ARE queryable**: `DOO_MESSAGES_B` (msg_request_id, msg_entity_type
  SRC_ORDER/SRC_LINE, msg_entity_id1=source order number) join `DOO_MESSAGES_TL` (message_text,
  language='US'). Other teams' import errors visible too.
- **REST `salesOrdersForOrderHub` WORKS for the integration user** (GET 200) — it is the prod
  order-creation path: delivered order TJYBV2M101 has `creation_mode=REST_salesOrdersForOrderHub`,
  created_by = OIC OAuth client id. (`salesOrders`/`draftOrders` remain 404 for our user.)
- REST create = plain POST to `/fscmRestApi/resources/11.13.18.05/salesOrdersForOrderHub`
  (no custom actions), JSON with `lines`, `shipToCustomer` (PartyId+SiteId), `billToCustomer`
  (CustomerAccountId+SiteUseId), `payments`, `additionalInformation` children.
- REST EFF shape (polymorphic on `Category`; contexts are child arrays named like the SOAP private
  VOs): header item `{"Category":"DOO_HEADERS_ADD_INFO",
  "HeaderEffBRevenue_5FManagement_5FInformation_5FHeaderprivateVO":[{"ContextCode":"Revenue_Management_Information_Header","channel":"1901"}]}`;
  line equivalent `DOO_FULFILL_LINES_ADD_INFO` +
  `FulfillLineEffBRevenue_5FManagement_5FInformation_5FLineprivateVO` (costCenter/productSegment).
  Describe chain: `…/describe?polymorphicType=salesOrdersForOrderHub.additionalInformation%3ADOO_HEADERS_ADD_INFO`.
- Housekeeping: a `stageOrders` batch named `TestPoD1` sits unprocessed in
  `DOO_ORDER_HEADERS_ALL_INT` (ORDER_REQUEST_ID 300000901415367) — inert unless the DOO import
  ESS job runs; ignore or purge later.

### REST create SOLVED (2026-09-28) — order TestPoD2 created (HTTP 201)

- **The pricing engine on dev1 cannot price anything right now**: every order created in the
  last 2 days (121) has `FREEZE_PRICE_FLAG='Y'`; all live-priced attempts fail with
  FOM-4515095 "can't identify a charge" for ANY item (19000101/19000028/19000009/19000103),
  regardless of PricingSegmentCode/PricingDate/PricingStrategyId.
- **Working recipe = freeze price + COMPLETE charge breakdown**. With FreezePriceFlag=true and
  no `charges`, OM still runs charge creation and fails. With charges present, the engine is
  skipped and the charge is validated instead.
- The charge validation error "list price or net price for charge X does not contain a value"
  means the charge needs BOTH components: `QP_LIST_PRICE`/`LIST_PRICE` **and**
  `QP_NET_PRICE`/`NET_PRICE` (unit + extended + header-currency amounts on each).
- Full working payload: `/tmp/rmcs_pod/create_order_payload.json` — header OMG/WP_B2C/B2C
  Customer 257035, shipTo PartyId 300000876780446+SiteId 300000876780450, billTo
  CustomerAccountId 300000876780448+SiteUseId 300000876780452, FreezePriceFlag=true,
  PricingSegmentCode='Y'; line item 19000103, org 3FED, TransactionCategoryCode=ORDER,
  UnitListPrice=UnitSellingPrice=ExtendedAmount=95, one charge (ORA_SALE/ORA_PRICE/
  QP_SALE_PRICE/PriceTypeCode ORA_ONE_TIME) with the two components.
- Created order: **TestPoD2**, HeaderId 300000901421333, line 1 LineId 300000901421337,
  FulfillLineId 300000901421336, item 19000103, $95.

### Fulfillment chain (dev1, 2026-09-28) — all verified working

- New orders sit NOT_STARTED until orchestration schedules them; can take ~20 min on dev1
  (queue lag). PATCHing the line (e.g. RequestedShipDate) also re-triggers it.
- Pick release: `POST /pickWaves` {SourceSystemName OPS, ShipFromOrganizationCode 3FED,
  OrderType "Sales order", OrderNumber, PickReleaseFlag true, ReleaseStatus All,
  CreateShipmentsFlag true, AutoPickConfirmFlag false, ReleaseMode ONLINE, BatchPrefix}.
  Verify in `wsh_delivery_details` by `source_header_number` (released_status S, batch_id,
  move_order_line_id). Note: `source_line_id` there is WSH's own id, NOT the DOO line id.
- ALL WP frame items are serial-controlled ("Dynamic entry at inventory receipt") — pick
  confirm MUST carry a serial. Find available ones in BIP-visible `inv_serial_numbers`
  (`current_status = 3` = in stores; no subinventory column). `mtl_serial_numbers` and
  `mtl_txn_request_*` are NOT BIP-visible.
- Pick slip lookup: REST `pickSlipDetails?q=Order='<order>'` → `pickSlipDetails/{id}/child/pickLines`
  (PickSlip, PickSlipLine, SourceSubinventory). Confirm: `POST /pickTransactions`
  {RollbackAllLinesOnError Y, OverpickAndMoveFlag false, pickLines:[{PickSlip, PickSlipLine,
  SubinventoryCode, PickedQuantity, serialItemSerials:[{FromSerialNumber, ToSerialNumber}]}]}.
- Ship confirm: find delivery in `wsh_new_deliveries` by `organization_id` + recent
  creation_date (source_header_id is the WSH order id from the pickWaves response, NOT the
  DOO header id), then `POST /shippingTransactions` {ShipmentName, Action CONFIRM,
  Organization 3FED}. DOO line goes SHIPPED → AWAIT_BILLING within ~1 min.
- Delivery date (WP_B2C PoD date source): order-hub `lineDetails` PATCH is DISABLED after
  ship ("action update is not enabled"). Working path: `POST /shipmentTransactionRequests`
  {ActionCode: "ShipmentUpdate", shipments:[{Shipment, ShipmentId, ActualDeliveryDate,
  SourceName: "OPS"}]} → sets `doo_fulfill_line_details.actual_delivery_date`.
- TestPoD2 end state: fulfill line 300000901421336 AWAIT_BILLING, fulfilled_qty 1,
  fulfillment/ship/delivery dates all 2026-09-28, serial M1910300015, shipment 1509152.

### RMCS contract identification gate (dev1, 2026-09-28) — root cause of "no PoD rows"

- TestPoD2 loaded cleanly into RMCS (doc 34003 / line 37011 / sub line 27011, all PROCESSED,
  no rows in `vrm_source_doc_errors`), but `IdentifyContractObligation` (ESS, params
  `300000003994590,D,<month-end>,D,N,N,N,N,#NULL`) repeatedly created NO contract/obligation
  for it — same for every line without the RM EFFs since 9/17.
- **Perfect dev1 correlation**: all 203 identified lines have line EFF cost_center
  (`vrm_source_doc_lines.src_attribute_char1`); 0 of 27 lines without it ever identified.
  Exceptions with cost center but no contract are all `ORA_RETURN_LINE` (returns don't
  identify standalone) or pre-rule July/August rows.
- The EFFs come from the order itself: header `DOO_HEADERS_EFF_B` context
  `Revenue_Management_Information_Header` (channel) and fulfill-line `DOO_FULFILL_LINES_EFF_B`
  context `Revenue_Management_Information_Line` (costCenter/productSegment). The order-hub
  REST API does NOT expose them after creation (PATCH 400/404; GET on EFF-carrying orders
  shows only the DOO_*_ADD_INFO category) — they must be set IN the create payload.
- **REST create WITH EFFs works**: polymorphic `additionalInformation` shape (per the notes
  above) accepted in the POST — TestPoD3 (HeaderId 300000901444212, line 300000901444216,
  fulfill 300000901444215) created with channel=90001, costCenter=3FED, productSegment=1301,
  verified in `DOO_HEADERS_EFF_B`/`DOO_FULFILL_LINES_EFF_B`.
- ESS job log retrieval: `erpintegrations` op `getESSExecutionDetails` returns the child
  request tree (JSON inside RequestStatus); `downloadESSJobExecutionDetailsRF` returns no
  content for these jobs.
- Period check: Sep-26 open for GL(101)/AP(200)/RMCS(10455); AR(222) is Future — does not
  block identification (9/16 identifications prove it).

### END-TO-END SUCCESS (dev1, 2026-09-28) — TestPoD3 produces a PoD row

- Full chain verified: REST create WITH EFFs → orchestration (PATCH line RequestedShipDate to
  re-trigger after DOO-2686198) → pickWaves (batch TESTPOD3-2138771) → pickTransactions with
  serial M1910300019 (slip 2039449) → shippingTransactions CONFIRM (delivery 1508157) →
  shipmentTransactionRequests ShipmentUpdate ActualDeliveryDate → stage Lambda
  `/rmcs/contract-creation` {"sales_order_numbers":"TestPoD3"} → RMCS doc line 37012 PROCESSED
  WITH cost_center/product_segment → callback chain ran Identify → **contract 36026,
  obligation 23001**.
- PoD query (`WP_RMCS_PROOF_OF_DELIVERY_DM.sql`, P_ORDER_NUMBERS=TestPoD3) returns exactly
  1 row: line_id 300000901444216, line_number 1, sub_line_id 3602637012 (= contract 36026 ||
  doc line 37012), satisfied_qty 1, fulfillment_date 2026-09-28 (delivery date, WP_B2C rule).
- TestPoD2 (no EFFs) stays un-identified in RMCS — inert backlog line, same as the other 27.
- Deployed report run via ExternalReportWSSService fails on catalog permissions for the
  integration user (`wp_scm_integration_user does not have permission to run the report`);
  the paired repo `.sql` is the same query and is what was validated.
- Repeatable test-data recipe = `create_order_pod3.json` pattern (REST create with the
  polymorphic EFF `additionalInformation` blocks) + the fulfillment chain above.
- This session's findings are captured in skills: new `om-order-lifecycle` (order
  create→deliver chain) and `rmcs-test-data` (EFF gate, VRM cheatsheet, PoD eligibility);
  `fusion-sql` gained `run_bip_report.py` + the NULL-column caveat; `erp-oeh` gained the
  ESS job operations (`submitESSJobRequest`/`getESSJobStatus`/`getESSExecutionDetails`).

### TestPoD4 dead end → TestPoD5 success (dev1, 2026-09-28 evening)

- **TestPoD4** (header 300000901473121, line 300000901473125, contract 36038, obligation
  23001): fully loaded/identified, but NOT PoD-eligible — `doo_fulfill_line_details
  .actual_delivery_date` is NULL forever. The ShipmentUpdate was sent 18s BEFORE the
  ship-confirm import created the DOO detail row (17:13:19 vs 17:13:37); the
  delivery-date fulfillment response was lost, and the WSH delivery date is set-once
  (later updates "succeed" but never change the stored value — verified with same value,
  midnight, previous day, next day; a date before the ship date is silently rejected).
- **Winning sequence (TestPoD2 pattern, confirmed by TestPoD5)**: ship confirm → WAIT
  for the SHIPPED row in `doo_fulfill_line_details` → THEN ShipmentUpdate → the date
  lands on the DOO row within minutes (`ImportOrderFulfillmentResponseJob`).
- **TestPoD5** (header 300000901544225, line 300000901544229, fulfill 300000901544228,
  serial M1910300018, delivery 1509161, delivery date 2026-09-28 20:03): RMCS doc line
  38012 PROCESSED with EFFs → contract 37015, obligation 24001 → PoD query returns
  exactly 1 row (sub_line_id 3701538012, qty 1, fulfillment_date = delivery date).
- Orchestration note: PATCHing a line while it is in DOO-2686198 fails with that same
  error — wait ~90 s and retry the PATCH.
- The stage Lambda's order-details read (deployed `WP RMCS Order Details Sales and RMA
  Report.xdo`) intermittently 504s/times out at the Akamai edge while the same SQL via
  the arbiter runs in ~3 s — transient pod report-path degradation; retry the Lambda.
- `doo_headers_all` shows 3 rows per REST order (1 OPEN + 2 DOO_REFERENCE orchestration
  copies with their own line ids); harmless — only the OPEN header's lines load to RMCS.

## Query for getting Validate Customer Contract results

### Changes (22/09/2026)
- key logic


### Query
```sql
-- RMCS-I-3001 - Validate Customer Contract Source Data status / errors
--
-- Parameters (same pattern as WP_GET_RECEIPT_REFUND_INFORMATION):
--   :P_FROM_DATE       DATE (optional; use with :P_TO_DATE)
--   :P_TO_DATE         DATE (optional; use with :P_FROM_DATE)
--   :P_REQUEST_IDS     multi-value LOV (optional) — VRMPRCBLS child REQUEST_ID and/or
--                      FBDI LOAD_REQUEST_ID (the ids stamped on the interface row)
--
SELECT
    'HEADER' AS line_level,
    h.document_id AS surrogate_id,
    h.document_id,
    CAST(NULL AS NUMBER) AS document_line_id,
    CAST(NULL AS NUMBER) AS document_sub_line_id,
    CAST(NULL AS NUMBER) AS document_additional_sline_id,
    h.source_system,
    h.document_type_code,
    h.data_transformation_status,
    h.data_trans_error_message,
    e.error_message_code,
    h.request_id,
    h.load_request_id,
    h.document_number,
    h.doc_id_int_1 AS nat_key_int_1,
    h.doc_id_int_2 AS nat_key_int_2,
    h.doc_id_int_3 AS nat_key_int_3,
    h.doc_id_int_4 AS nat_key_int_4,
    h.doc_id_int_5 AS nat_key_int_5,
    h.doc_id_char_1 AS nat_key_char_1,
    h.doc_id_char_2 AS nat_key_char_2,
    h.doc_id_char_3 AS nat_key_char_3,
    h.doc_id_char_4 AS nat_key_char_4,
    h.doc_id_char_5 AS nat_key_char_5,
    CAST(NULL AS NUMBER) AS parent_line_id_int_1,
    CAST(NULL AS NUMBER) AS parent_line_id_int_2,
    CAST(NULL AS VARCHAR2(30)) AS parent_line_id_char_1
FROM
    vrm_source_documents h
    INNER JOIN ess_request_history ess
        ON ess.requestid = h.request_id
       AND ess.name = 'VRMPRCBLS'
    LEFT JOIN vrm_source_doc_errors e
        ON e.error_line_id = h.document_id
       AND e.error_line_level = 'H'
WHERE
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND h.last_update_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE)
    )
    OR h.request_id IN (:P_REQUEST_IDS)
    OR h.load_request_id IN (:P_REQUEST_IDS)
UNION ALL
SELECT
    'LINE',
    l.document_line_id,
    l.document_id,
    l.document_line_id,
    CAST(NULL AS NUMBER),
    CAST(NULL AS NUMBER),
    l.source_system,
    l.document_type_code,
    l.data_transformation_status,
    l.data_trans_error_message,
    e.error_message_code,
    l.request_id,
    l.load_request_id,
    CAST(NULL AS VARCHAR2(300)),
    l.doc_line_id_int_1,
    l.doc_line_id_int_2,
    l.doc_line_id_int_3,
    l.doc_line_id_int_4,
    l.doc_line_id_int_5,
    l.doc_line_id_char_1,
    l.doc_line_id_char_2,
    l.doc_line_id_char_3,
    l.doc_line_id_char_4,
    l.doc_line_id_char_5,
    CAST(NULL AS NUMBER),
    CAST(NULL AS NUMBER),
    CAST(NULL AS VARCHAR2(30))
FROM
    vrm_source_doc_lines l
    INNER JOIN ess_request_history ess
        ON ess.requestid = l.request_id
       AND ess.name = 'VRMPRCBLS'
    LEFT JOIN vrm_source_doc_errors e
        ON e.error_line_id = l.document_line_id
       AND e.error_line_level = 'L'
WHERE
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND l.last_update_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE)
    )
    OR l.request_id IN (:P_REQUEST_IDS)
    OR l.load_request_id IN (:P_REQUEST_IDS)
UNION ALL
SELECT
    'SUBLINE',
    s.document_sub_line_id,
    s.document_id,
    s.document_line_id,
    s.document_sub_line_id,
    CAST(NULL AS NUMBER),
    s.source_system,
    s.document_type_code,
    s.data_transformation_status,
    s.data_trans_error_message,
    e.error_message_code,
    s.request_id,
    s.load_request_id,
    CAST(NULL AS VARCHAR2(300)),
    s.doc_sub_line_id_int_1,
    s.doc_sub_line_id_int_2,
    s.doc_sub_line_id_int_3,
    s.doc_sub_line_id_int_4,
    s.doc_sub_line_id_int_5,
    s.doc_sub_line_id_char_1,
    s.doc_sub_line_id_char_2,
    s.doc_sub_line_id_char_3,
    s.doc_sub_line_id_char_4,
    s.doc_sub_line_id_char_5,
    s.doc_line_id_int_1,
    s.doc_line_id_int_2,
    s.doc_line_id_char_1
FROM
    vrm_source_doc_sub_lines s
    INNER JOIN ess_request_history ess
        ON ess.requestid = s.request_id
       AND ess.name = 'VRMPRCBLS'
    LEFT JOIN vrm_source_doc_errors e
        ON e.error_line_id = s.document_sub_line_id
       AND e.error_line_level = 'S'
WHERE
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND s.last_update_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE)
    )
    OR s.request_id IN (:P_REQUEST_IDS)
    OR s.load_request_id IN (:P_REQUEST_IDS)
UNION ALL
SELECT
    'ADDL_SUBLINE',
    a.document_additional_sline_id,
    a.document_id,
    a.document_line_id,
    CAST(NULL AS NUMBER),
    a.document_additional_sline_id,
    a.source_system,
    a.document_type_code,
    a.data_transformation_status,
    CAST(NULL AS VARCHAR2(1000)),
    e.error_message_code,
    a.request_id,
    a.load_request_id,
    CAST(NULL AS VARCHAR2(300)),
    a.doc_additional_sline_id_int_1,
    a.doc_additional_sline_id_int_2,
    a.doc_additional_sline_id_int_3,
    a.doc_additional_sline_id_int_4,
    a.doc_additional_sline_id_int_5,
    a.doc_additional_sline_id_char_1,
    a.doc_additional_sline_id_char_2,
    a.doc_additional_sline_id_char_3,
    a.doc_additional_sline_id_char_4,
    a.doc_additional_sline_id_char_5,
    a.doc_line_id_int_1,
    a.doc_line_id_int_2,
    a.doc_line_id_char_1
FROM
    vrm_source_doc_addl_sublines a
    INNER JOIN ess_request_history ess
        ON ess.requestid = a.request_id
       AND ess.name = 'VRMPRCBLS'
    LEFT JOIN vrm_source_doc_errors e
        ON e.error_line_id = a.document_additional_sline_id
       AND e.error_line_level = 'A'
WHERE
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND a.last_update_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE)
    )
    OR a.request_id IN (:P_REQUEST_IDS)
    OR a.load_request_id IN (:P_REQUEST_IDS)
ORDER BY
    1,  -- line_level
    2,  -- surrogate_id
    11 -- error_message_code

```

### Probing
```sql
SELECT
  a.DOCUMENT_ADDITIONAL_SLINE_ID,
  a.DATA_TRANSFORMATION_STATUS,
  a.REQUEST_ID,
  a.LOAD_REQUEST_ID,
  a.SOURCE_SYSTEM,
  a.DOCUMENT_TYPE_CODE,
  a.DOC_ADDITIONAL_SLINE_ID_INT_1,
  a.DOC_LINE_ID_INT_1,
  a.DOC_LINE_ID_INT_2,
  a.DOC_LINE_ID_CHAR_1,
  e.ERROR_LINE_LEVEL,
  e.ERROR_MESSAGE_CODE,
  e.LOAD_REQUEST_ID AS error_load_request_id
FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
LEFT JOIN VRM_SOURCE_DOC_ERRORS e
  ON e.ERROR_LINE_ID = a.DOCUMENT_ADDITIONAL_SLINE_ID
 AND e.ERROR_LINE_LEVEL = 'A'
WHERE a.LOAD_REQUEST_ID = 111610505
ORDER BY a.DOCUMENT_ADDITIONAL_SLINE_ID;


SELECT 'HEADER' AS line_level,
       h.DOCUMENT_ID AS surrogate_id,
       h.DATA_TRANSFORMATION_STATUS,
       h.REQUEST_ID,
       h.LOAD_REQUEST_ID,
       h.SOURCE_SYSTEM,
       h.DOCUMENT_TYPE_CODE
FROM VRM_SOURCE_DOCUMENTS h
WHERE h.LOAD_REQUEST_ID = 111610505
UNION ALL
SELECT 'LINE', l.DOCUMENT_LINE_ID, l.DATA_TRANSFORMATION_STATUS,
       l.REQUEST_ID, l.LOAD_REQUEST_ID, l.SOURCE_SYSTEM, l.DOCUMENT_TYPE_CODE
FROM VRM_SOURCE_DOC_LINES l
WHERE l.LOAD_REQUEST_ID = 111610505
UNION ALL
SELECT 'SUBLINE', s.DOCUMENT_SUB_LINE_ID, s.DATA_TRANSFORMATION_STATUS,
       s.REQUEST_ID, s.LOAD_REQUEST_ID, s.SOURCE_SYSTEM, s.DOCUMENT_TYPE_CODE
FROM VRM_SOURCE_DOC_SUB_LINES s
WHERE s.LOAD_REQUEST_ID = 111610505
UNION ALL
SELECT 'ADDL_SUBLINE', a.DOCUMENT_ADDITIONAL_SLINE_ID, a.DATA_TRANSFORMATION_STATUS,
       a.REQUEST_ID, a.LOAD_REQUEST_ID, a.SOURCE_SYSTEM, a.DOCUMENT_TYPE_CODE
FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
WHERE a.LOAD_REQUEST_ID = 111610505
ORDER BY 1, 2;

SELECT 'ADDL_BY_REQUEST' AS q, COUNT(*) AS cnt
FROM VRM_SOURCE_DOC_ADDL_SUBLINES WHERE REQUEST_ID = 111622047
UNION ALL
SELECT 'ADDL_BY_LOAD', COUNT(*)
FROM VRM_SOURCE_DOC_ADDL_SUBLINES WHERE LOAD_REQUEST_ID = 111610505
UNION ALL
SELECT 'LINE_BY_REQUEST_111622047', COUNT(*)
FROM VRM_SOURCE_DOC_LINES WHERE REQUEST_ID = 111622047
UNION ALL
SELECT 'LINE_BY_LOAD_111610505', COUNT(*)
FROM VRM_SOURCE_DOC_LINES WHERE LOAD_REQUEST_ID = 111610505;

SELECT
  r.REQUESTID,
  r.ABSPARENTID,
  r.PARENTREQUESTID,
  r.INSTANCEPARENTID,
  r.APPLICATION,
  r.NAME,
  r.DEFINITION,
  r.STATE,
  r.PROCESSSTART,
  r.PROCESSEND
FROM ESS_REQUEST_HISTORY r
WHERE r.REQUESTID IN (111622047, 111666806, 111666789, 111666787, 111666790)
ORDER BY r.REQUESTID;

SELECT
  r.REQUESTID,
  r.ABSPARENTID,
  r.PARENTREQUESTID,
  r.DEFINITION,
  r.STATE,
  r.PROCESSSTART,
  r.PROCESSEND
FROM ESS_REQUEST_HISTORY r
WHERE r.ABSPARENTID = (
        SELECT ABSPARENTID
        FROM ESS_REQUEST_HISTORY
        WHERE REQUESTID = 111666806
      )
ORDER BY r.REQUESTID;


SELECT
  rh.REQUESTID,
  rh.PARENTREQUESTID,
  rh.NAME,
  rh.DEFINITION,
  rh.EXECUTABLE_STATUS,
  rh.PROCESSSTART,
  rh.PROCESSEND
FROM FUSION_ORA_ESS.REQUEST_HISTORY_VIEW rh
WHERE rh.REQUESTID IN (111622047, 111666806, 111666789, 111666787, 111666790)
ORDER BY rh.REQUESTID;


SELECT l.DOCUMENT_LINE_ID, l.DATA_TRANSFORMATION_STATUS, l.REQUEST_ID,
       l.LOAD_REQUEST_ID, l.SOURCE_SYSTEM, e.ERROR_MESSAGE_CODE
FROM VRM_SOURCE_DOC_LINES l
LEFT JOIN VRM_SOURCE_DOC_ERRORS e
  ON e.ERROR_LINE_ID = l.DOCUMENT_LINE_ID AND e.ERROR_LINE_LEVEL = 'L'
WHERE l.REQUEST_ID = 111666787
FETCH FIRST 30 ROWS ONLY;





-- Probe A: status distribution per level (no request filter)
SELECT 'HEADER' AS line_level,
       h.DATA_TRANSFORMATION_STATUS,
       COUNT(*) AS cnt,
       MIN(h.LAST_UPDATE_DATE) AS oldest_upd,
       MAX(h.LAST_UPDATE_DATE) AS newest_upd
FROM VRM_SOURCE_DOCUMENTS h
GROUP BY h.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'LINE', l.DATA_TRANSFORMATION_STATUS, COUNT(*),
       MIN(l.LAST_UPDATE_DATE), MAX(l.LAST_UPDATE_DATE)
FROM VRM_SOURCE_DOC_LINES l
GROUP BY l.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'SUBLINE', s.DATA_TRANSFORMATION_STATUS, COUNT(*),
       MIN(s.LAST_UPDATE_DATE), MAX(s.LAST_UPDATE_DATE)
FROM VRM_SOURCE_DOC_SUB_LINES s
GROUP BY s.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'ADDL_SUBLINE', a.DATA_TRANSFORMATION_STATUS, COUNT(*),
       MIN(a.LAST_UPDATE_DATE), MAX(a.LAST_UPDATE_DATE)
FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
GROUP BY a.DATA_TRANSFORMATION_STATUS
ORDER BY 1, 2;

-- Probe B: recent non-blank / interesting-status samples across all levels
-- (adjust NVL list after Probe A shows real status codes)
SELECT *
FROM (
  SELECT 'HEADER' AS line_level,
         h.DATA_TRANSFORMATION_STATUS,
         h.REQUEST_ID,
         h.LOAD_REQUEST_ID,
         h.SOURCE_SYSTEM,
         h.DOCUMENT_TYPE_CODE,
         h.DOCUMENT_ID AS surrogate_id,
         h.LAST_UPDATE_DATE
  FROM VRM_SOURCE_DOCUMENTS h
  WHERE h.DATA_TRANSFORMATION_STATUS IS NOT NULL
  UNION ALL
  SELECT 'LINE', l.DATA_TRANSFORMATION_STATUS, l.REQUEST_ID, l.LOAD_REQUEST_ID,
         l.SOURCE_SYSTEM, l.DOCUMENT_TYPE_CODE, l.DOCUMENT_LINE_ID, l.LAST_UPDATE_DATE
  FROM VRM_SOURCE_DOC_LINES l
  WHERE l.DATA_TRANSFORMATION_STATUS IS NOT NULL
  UNION ALL
  SELECT 'SUBLINE', s.DATA_TRANSFORMATION_STATUS, s.REQUEST_ID, s.LOAD_REQUEST_ID,
         s.SOURCE_SYSTEM, s.DOCUMENT_TYPE_CODE, s.DOCUMENT_SUB_LINE_ID, s.LAST_UPDATE_DATE
  FROM VRM_SOURCE_DOC_SUB_LINES s
  WHERE s.DATA_TRANSFORMATION_STATUS IS NOT NULL
  UNION ALL
  SELECT 'ADDL_SUBLINE', a.DATA_TRANSFORMATION_STATUS, a.REQUEST_ID, a.LOAD_REQUEST_ID,
         a.SOURCE_SYSTEM, a.DOCUMENT_TYPE_CODE, a.DOCUMENT_ADDITIONAL_SLINE_ID, a.LAST_UPDATE_DATE
  FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
  WHERE a.DATA_TRANSFORMATION_STATUS IS NOT NULL
)
ORDER BY LAST_UPDATE_DATE DESC NULLS LAST
FETCH FIRST 100 ROWS ONLY;

-- Probe C: focus on likely failure statuses (widen/narrow after Probe A)
-- Common candidates: Rejected, Unprocessed, and any non-Processed codes seen in A
SELECT 'ADDL_SUBLINE' AS line_level,
       a.DOCUMENT_ADDITIONAL_SLINE_ID,
       a.SOURCE_SYSTEM,
       a.DOCUMENT_TYPE_CODE,
       a.DATA_TRANSFORMATION_STATUS,
       a.REQUEST_ID,
       a.LOAD_REQUEST_ID,
       a.DOC_ADDITIONAL_SLINE_ID_INT_1,
       a.DOC_LINE_ID_INT_1,
       a.DOC_LINE_ID_INT_2,
       a.DOC_LINE_ID_CHAR_1,
       a.LAST_UPDATE_DATE
FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
WHERE UPPER(NVL(a.DATA_TRANSFORMATION_STATUS, 'X')) NOT IN ('PROCESSED', 'PURGED', 'X')
ORDER BY a.LAST_UPDATE_DATE DESC NULLS LAST
FETCH FIRST 50 ROWS ONLY;

-- Probe D: VRM_SOURCE_DOC_ERRORS population (no request filter)
SELECT e.ERROR_LINE_LEVEL,
       e.ERROR_MESSAGE_CODE,
       COUNT(*) AS cnt,
       MIN(e.CREATION_DATE) AS oldest,
       MAX(e.CREATION_DATE) AS newest,
       MIN(e.LOAD_REQUEST_ID) AS min_load_req,
       MAX(e.LOAD_REQUEST_ID) AS max_load_req
FROM VRM_SOURCE_DOC_ERRORS e
GROUP BY e.ERROR_LINE_LEVEL, e.ERROR_MESSAGE_CODE
ORDER BY cnt DESC;

```


## Query for getting additional sublines RMCS-I-3001
```sql
WITH load_ids AS (
  SELECT 116724393 AS load_request_id FROM DUAL UNION ALL  -- Load Interface File for Import
  SELECT 116724394 FROM DUAL UNION ALL                     -- Transfer File
  SELECT 116724395 FROM DUAL                               -- Load File to Interface (most likely)
)
SELECT 'VRM_SOURCE_DOCUMENTS' AS table_name,
       d.LOAD_REQUEST_ID,
       d.DATA_TRANSFORMATION_STATUS,
       COUNT(*) AS row_count
FROM VRM_SOURCE_DOCUMENTS d
JOIN load_ids i ON i.load_request_id = d.LOAD_REQUEST_ID
GROUP BY d.LOAD_REQUEST_ID, d.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'VRM_SOURCE_DOC_LINES',
       l.LOAD_REQUEST_ID,
       l.DATA_TRANSFORMATION_STATUS,
       COUNT(*)
FROM VRM_SOURCE_DOC_LINES l
JOIN load_ids i ON i.load_request_id = l.LOAD_REQUEST_ID
GROUP BY l.LOAD_REQUEST_ID, l.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'VRM_SOURCE_DOC_SUB_LINES',
       s.LOAD_REQUEST_ID,
       s.DATA_TRANSFORMATION_STATUS,
       COUNT(*)
FROM VRM_SOURCE_DOC_SUB_LINES s
JOIN load_ids i ON i.load_request_id = s.LOAD_REQUEST_ID
GROUP BY s.LOAD_REQUEST_ID, s.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'VRM_SOURCE_DOC_ADDL_SUBLINES',
       a.LOAD_REQUEST_ID,
       a.DATA_TRANSFORMATION_STATUS,
       COUNT(*)
FROM VRM_SOURCE_DOC_ADDL_SUBLINES a
JOIN load_ids i ON i.load_request_id = a.LOAD_REQUEST_ID
GROUP BY a.LOAD_REQUEST_ID, a.DATA_TRANSFORMATION_STATUS
UNION ALL
SELECT 'VRM_SOURCE_DOC_ERRORS',
       e.LOAD_REQUEST_ID,
       NULL,
       COUNT(*)
FROM VRM_SOURCE_DOC_ERRORS e
JOIN load_ids i ON i.load_request_id = e.LOAD_REQUEST_ID
GROUP BY e.LOAD_REQUEST_ID
ORDER BY 1, 2;

-- select table
SELECT
    LOAD_REQUEST_ID,
    DATA_TRANSFORMATION_STATUS,  -- or DATA_TRANSFORMATION_STATUS
    DOCUMENT_TYPE_CODE,
    SOURCE_SYSTEM,
    -- DOC_ADDL_SUBLINE_ID_INT_1,
    DOC_LINE_ID_INT_1,
    DOC_LINE_ID_INT_2,
    DOC_LINE_ID_CHAR_1
    -- ADDITIONAL_SATISFACTION_EVENT_TYPE_CODE,
    -- FULFILLMENT_DATE,
    -- SATISFIED_QUANTITY
FROM VRM_SOURCE_DOC_ADDL_SUBLINES
WHERE LOAD_REQUEST_ID IN (116724393, 116724394, 116724395);

-- select code for FBDI
SELECT
    ERP_INTERFACE_OPTIONS_ID,
    ERP_INTERFACE_DETAILS_ID,
    CONTROL_FILE_NAME,
    DATA_FILE_NAME_PREFIX,
    INTERFACE_TABLE_NAMES
FROM FUN_ERP_INTERFACE_DETAILS
WHERE LOWER(CONTROL_FILE_NAME) LIKE '%vrmrevenue%'
   OR LOWER(DATA_FILE_NAME_PREFIX) LIKE '%vrmrbl%';

-- get DOO_HEADERS_ALL.ORDER_TYPE_CODE e.g. WP_B2C, WP_B2C_CPU, WP_B2C_TAKEAWAY, WP_B2B_WHOLESALE
SELECT lookup_code,
       meaning,
       description,
       tag,
       enabled_flag
FROM   fnd_lookup_values_vl
WHERE  lookup_type = 'ORA_DOO_ORDER_TYPES'
ORDER BY display_sequence, meaning;


-- get doo_fulfill_lines_all.status_code e.g 'SHIPPED', 'AWAITING_BILLING', 'BILLED'
SELECT s.status_code,
       s.display_name
FROM   doo_statuses_vl s
WHERE  s.orchestration_application_id = 10008   -- fulfill line statuses
ORDER BY s.display_name;
```

```sql
-- RMCS-I-3001 - Run each step in BI Publisher to find where row count drops to zero.  
-- Replace '42' with a known sales order number (e.g. :P_ORDER_NUMBERS value).  
--  
-- 1) Funnel counts  
SELECT '1_base_fulfill_lines' AS step, COUNT(*) AS row_count  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
WHERE h.source_order_number = '42'  
  
UNION ALL  
  
SELECT '2_status_filter', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  
UNION ALL  
  
SELECT '3_qty_filter', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  AND NVL(fl.fulfilled_qty, 0) > 0  
  
UNION ALL  
  
SELECT '4_rmcs_line_join', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
INNER JOIN vrm_source_doc_lines sdl  
    ON sdl.doc_line_id_char_1 = h.source_order_number  
   AND sdl.doc_line_id_int_1 = l.line_id  
   AND sdl.doc_line_id_int_2 = l.line_number  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  AND NVL(fl.fulfilled_qty, 0) > 0  
  
UNION ALL  
  
SELECT '5_perf_obligation_join', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
INNER JOIN vrm_source_doc_lines sdl  
    ON sdl.doc_line_id_char_1 = h.source_order_number  
   AND sdl.doc_line_id_int_1 = l.line_id  
   AND sdl.doc_line_id_int_2 = l.line_number  
INNER JOIN vrm_perf_obligation_lines pol  
    ON pol.document_line_id = sdl.document_line_id  
   AND NVL(pol.removed_flag, 'N') = 'N'  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  AND NVL(fl.fulfilled_qty, 0) > 0  
  
UNION ALL  
  
SELECT '6_not_already_uploaded', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
INNER JOIN vrm_source_doc_lines sdl  
    ON sdl.doc_line_id_char_1 = h.source_order_number  
   AND sdl.doc_line_id_int_1 = l.line_id  
   AND sdl.doc_line_id_int_2 = l.line_number  
INNER JOIN vrm_perf_obligation_lines pol  
    ON pol.document_line_id = sdl.document_line_id  
   AND NVL(pol.removed_flag, 'N') = 'N'  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  AND NVL(fl.fulfilled_qty, 0) > 0  
  AND NOT EXISTS (  
      SELECT 1 FROM vrm_source_doc_addl_sublines ads  
      WHERE ads.document_line_id = sdl.document_line_id  
        AND ads.doc_additional_sline_id_int_1 = TO_NUMBER(  
            TO_CHAR(pol.customer_contract_header_id) || TO_CHAR(pol.document_line_id))  
        AND UPPER(ads.additional_se_type_code) LIKE '%PROOF%DELIVERY%'  
  )  
  
UNION ALL  
  
SELECT '7_date_not_null_by_type', COUNT(*)  
FROM doo_headers_all h  
INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
INNER JOIN doo_fulfill_lines_all fl  
    ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
LEFT JOIN (  
    SELECT fulfill_line_id, MAX(actual_delivery_date) AS actual_delivery_date  
    FROM doo_fulfill_line_details  
    WHERE actual_delivery_date IS NOT NULL  
    GROUP BY fulfill_line_id  
) fld ON fld.fulfill_line_id = fl.fulfill_line_id  
INNER JOIN vrm_source_doc_lines sdl  
    ON sdl.doc_line_id_char_1 = h.source_order_number  
   AND sdl.doc_line_id_int_1 = l.line_id  
   AND sdl.doc_line_id_int_2 = l.line_number  
INNER JOIN vrm_perf_obligation_lines pol  
    ON pol.document_line_id = sdl.document_line_id  
   AND NVL(pol.removed_flag, 'N') = 'N'  
WHERE h.source_order_number = '42'  
  AND fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
  AND NVL(fl.fulfilled_qty, 0) > 0  
  AND NOT EXISTS (  
      SELECT 1 FROM vrm_source_doc_addl_sublines ads  
      WHERE ads.document_line_id = sdl.document_line_id  
        AND ads.doc_additional_sline_id_int_1 = TO_NUMBER(  
            TO_CHAR(pol.customer_contract_header_id) || TO_CHAR(pol.document_line_id))  
        AND UPPER(ads.additional_se_type_code) LIKE '%PROOF%DELIVERY%'  
  )  
  AND CASE  
      WHEN h.order_type_code IN ('WP_B2C', 'WP_B2C_CPU') THEN fld.actual_delivery_date  
      WHEN h.order_type_code = 'WP_B2C_TAKEAWAY' THEN fl.fulfillment_date  
      WHEN h.order_type_code = 'WP_B2B_WHOLESALE' THEN fl.actual_ship_date  
  END IS NOT NULL  
  
ORDER BY 1;  
  
-- 2) Per-line pass/fail flags (run separately)  
-- SELECT  
--     h.source_order_number,  
--     h.order_type_code,  
--     l.line_id,  
--     l.line_number,  
--     fl.fulfill_line_id,  
--     fl.fulfill_line_number,  
--     fl.status_code,  
--     fl.fulfilled_qty,  
--     fld.actual_delivery_date,  
--     fl.fulfillment_date,  
--     fl.actual_ship_date,  
--     sdl.document_line_id AS rmcs_document_line_id,  
--     pol.document_line_id AS pol_document_line_id,  
--     pol.removed_flag,  
--     CASE WHEN fl.status_code IN ('SHIPPED', 'AWAIT_BILLING', 'BILLED', 'CLOSED')  
--          THEN 'Y' ELSE 'N' END AS pass_status,  
--     CASE WHEN NVL(fl.fulfilled_qty, 0) > 0 THEN 'Y' ELSE 'N' END AS pass_qty,  
--     CASE WHEN sdl.document_line_id IS NOT NULL THEN 'Y' ELSE 'N' END AS pass_rmcs_join,  
--     CASE WHEN pol.document_line_id IS NOT NULL AND NVL(pol.removed_flag, 'N') = 'N'  
--          THEN 'Y' ELSE 'N' END AS pass_pol,  
--     CASE WHEN EXISTS (  
--         SELECT 1 FROM vrm_source_doc_addl_sublines ads  
--         WHERE ads.document_line_id = sdl.document_line_id  
--           AND ads.doc_additional_sline_id_int_1 = TO_NUMBER(  
--               TO_CHAR(pol.customer_contract_header_id) || TO_CHAR(pol.document_line_id))  
--           AND UPPER(ads.additional_se_type_code) LIKE '%PROOF%DELIVERY%'  
--     ) THEN 'N' ELSE 'Y' END AS pass_not_uploaded,  
--     CASE WHEN CASE  
--         WHEN h.order_type_code IN ('WP_B2C', 'WP_B2C_CPU') THEN fld.actual_delivery_date  
--         WHEN h.order_type_code = 'WP_B2C_TAKEAWAY' THEN fl.fulfillment_date  
--         WHEN h.order_type_code = 'WP_B2B_WHOLESALE' THEN fl.actual_ship_date  
--     END IS NOT NULL THEN 'Y' ELSE 'N' END AS pass_date  
-- FROM doo_headers_all h  
-- INNER JOIN doo_lines_all l ON l.header_id = h.header_id  
-- INNER JOIN doo_fulfill_lines_all fl  
--     ON fl.header_id = h.header_id AND fl.line_id = l.line_id AND fl.shippable_flag = 'Y'  
-- LEFT JOIN (  
--     SELECT fulfill_line_id, MAX(actual_delivery_date) AS actual_delivery_date  
--     FROM doo_fulfill_line_details  
--     GROUP BY fulfill_line_id  
-- ) fld ON fld.fulfill_line_id = fl.fulfill_line_id  
-- LEFT JOIN vrm_source_doc_lines sdl  
--     ON sdl.doc_line_id_char_1 = h.source_order_number  
--    AND sdl.doc_line_id_int_1 = l.line_id  
--    AND sdl.doc_line_id_int_2 = l.line_number  
-- LEFT JOIN vrm_perf_obligation_lines pol  
--     ON pol.document_line_id = sdl.document_line_id  
-- WHERE h.source_order_number = '42'  
-- ORDER BY l.line_number, fl.fulfill_line_number;
```