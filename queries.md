## Query to get INBOUND_TO_SHIPMENT_NUMBER and INBOUND_TO_SHIPMENT_TRACKING_NUMBER

This is a query adadpted from WP_INBOUND_TRANSFER_ORDER_SHIPMENTS_TEMPLATE:
```
SELECT DISTINCT
    rsh.shipment_num        AS shipment_number,
    fwdd.tracking_number
FROM rcv_shipment_headers rsh
JOIN rcv_shipment_lines rsl
    ON rsl.shipment_header_id = rsh.shipment_header_id
   AND rsl.source_document_code = 'TRANSFER ORDER'
   AND rsl.shipment_line_id IS NOT NULL
   AND rsl.line_num IS NOT NULL
   AND rsl.item_id IS NOT NULL
   AND rsl.quantity_shipped IS NOT NULL
JOIN egp_system_items_b esib
    ON esib.organization_id = rsl.from_organization_id
   AND esib.inventory_item_id = rsl.item_id
JOIN wsh_new_deliveries fwnd
    ON fwnd.delivery_name = rsh.shipment_num
   AND fwnd.source_line_type = 'TRANSFER_ORDER'
JOIN wsh_delivery_assignments wda
    ON wda.delivery_id = fwnd.delivery_id
JOIN wsh_delivery_details fwdd
    ON fwdd.delivery_detail_id = wda.delivery_detail_id
   AND fwdd.source_line_type = 'TRANSFER_ORDER'
WHERE rsh.receipt_source_code = 'TRANSFER ORDER'
  AND fwdd.tracking_number IS NOT NULL
  AND rsh.creation_date >= TRUNC(SYSDATE) - 30   -- shrink if still slow (e.g. 7, 14)
ORDER BY rsh.shipment_num
FETCH FIRST 100 ROWS ONLY

--

WITH inbound_shipment_reference AS (
    SELECT
        fwnd.delivery_name   AS shipment_number,
        fwdd.tracking_number
    FROM wsh_delivery_assignments wda
    JOIN wsh_new_deliveries fwnd
        ON fwnd.delivery_id = wda.delivery_id
       AND fwnd.source_line_type = 'TRANSFER_ORDER'
    JOIN wsh_delivery_details fwdd
        ON fwdd.delivery_detail_id = wda.delivery_detail_id
       AND fwdd.source_line_type = 'TRANSFER_ORDER'
    WHERE fwdd.tracking_number IS NOT NULL
)
SELECT DISTINCT
    isr.shipment_number,
    isr.tracking_number
FROM inbound_shipment_reference isr
WHERE EXISTS (
        SELECT 1
        FROM rcv_shipment_headers rsh
        JOIN rcv_shipment_lines rsl
            ON rsl.shipment_header_id = rsh.shipment_header_id
           AND rsl.source_document_code = 'TRANSFER ORDER'
           AND rsl.shipment_line_id IS NOT NULL
           AND rsl.line_num IS NOT NULL
           AND rsl.item_id IS NOT NULL
           AND rsl.quantity_shipped IS NOT NULL
        JOIN egp_system_items_b esib
            ON esib.organization_id = rsl.from_organization_id
           AND esib.inventory_item_id = rsl.item_id
        WHERE rsh.shipment_num = isr.shipment_number
          AND rsh.receipt_source_code = 'TRANSFER ORDER'
    )
ORDER BY isr.shipment_number
FETCH FIRST 100 ROWS ONLY;

-- 
WITH inbound_shipment_reference AS (
    SELECT
        fwnd.delivery_name        AS shipment_number,
        fwdd.tracking_number
    FROM wsh_delivery_assignments wda
    JOIN wsh_new_deliveries fwnd
        ON fwnd.delivery_id = wda.delivery_id
       AND fwnd.source_line_type = 'TRANSFER_ORDER'
    JOIN wsh_delivery_details fwdd
        ON fwdd.delivery_detail_id = wda.delivery_detail_id
       AND fwdd.source_line_type = 'TRANSFER_ORDER'
)
SELECT DISTINCT
    isr.shipment_number,
    isr.tracking_number
FROM inbound_shipment_reference isr
JOIN rcv_shipment_headers rsh
    ON rsh.shipment_num = isr.shipment_number
   AND rsh.receipt_source_code = 'TRANSFER ORDER'
JOIN rcv_shipment_lines rsl
    ON rsl.shipment_header_id = rsh.shipment_header_id
   AND rsl.source_document_code = 'TRANSFER ORDER'
JOIN egp_system_items_b esib
    ON esib.organization_id = rsl.from_organization_id
   AND esib.inventory_item_id = rsl.item_id
WHERE isr.tracking_number IS NOT NULL
  AND rsl.shipment_line_id IS NOT NULL
  AND rsl.line_num IS NOT NULL
  AND rsl.item_id IS NOT NULL
  AND rsl.quantity_shipped IS NOT NULL
ORDER BY isr.shipment_number
FETCH FIRST 100 ROWS ONLY;

-- Shipment numbers that should produce DATA_DS with non-empty INBOUND_SHIPMENTS
-- and each shipment with at least one INBOUND_SHIPMENT_LINES row (incl. ITEM_NUMBER).
WITH inbound_shipment_reference AS (
    SELECT
        fwnd.delivery_name             AS shipment_number,
        fwdd.tracking_number,
        fwdd.source_header_number      AS transfer_order_number
    FROM wsh_delivery_assignments wda
    JOIN wsh_new_deliveries fwnd
        ON fwnd.delivery_id = wda.delivery_id
       AND fwnd.source_line_type = 'TRANSFER_ORDER'
    JOIN wsh_delivery_details fwdd
        ON fwdd.delivery_detail_id = wda.delivery_detail_id
       AND fwdd.source_line_type = 'TRANSFER_ORDER'
),
headers AS (
    SELECT DISTINCT
        isr.shipment_number,
        isr.tracking_number,
        isr.transfer_order_number,
        rsh.shipment_header_id
    FROM inbound_shipment_reference isr
    JOIN rcv_shipment_headers rsh
        ON rsh.shipment_num = isr.shipment_number
       AND rsh.receipt_source_code = 'TRANSFER ORDER'
)
SELECT DISTINCT
    h.shipment_number,
    h.tracking_number,
    h.transfer_order_number,
    h.shipment_header_id,
    COUNT(DISTINCT rsl.shipment_line_id) AS inbound_line_count
FROM headers h
JOIN rcv_shipment_lines rsl
    ON rsl.shipment_header_id = h.shipment_header_id
   AND rsl.source_document_code = 'TRANSFER ORDER'
JOIN egp_system_items_b esib
    ON esib.organization_id = rsl.from_organization_id
   AND esib.inventory_item_id = rsl.item_id
WHERE rsl.shipment_line_id IS NOT NULL
  AND rsl.line_num IS NOT NULL
  AND rsl.item_id IS NOT NULL
  AND rsl.quantity_shipped IS NOT NULL
GROUP BY
    h.shipment_number,
    h.tracking_number,
    h.transfer_order_number,
    h.shipment_header_id
HAVING COUNT(DISTINCT rsl.shipment_line_id) >= 1
ORDER BY h.shipment_number
FETCH FIRST 100 ROWS ONLY;
```


## Query to get ShipmentLine statuses

```
SELECT
    flv.lookup_type,
    flv.lookup_code,
    flv.meaning,
    flv.description,
    flv.enabled_flag,
    flv.start_date_active,
    flv.end_date_active
FROM
    fnd_lookup_values flv
WHERE
    flv.lookup_type = 'WSH_PICK_STATUS'
    AND flv.enabled_flag = 'Y'
    AND flv.language = USERENV('LANG') 
ORDER BY
    flv.lookup_code
```

|                 |             |                              |                                                                                                    |              |                               |                 |
| --------------- | ----------- | ---------------------------- | -------------------------------------------------------------------------------------------------- | ------------ | ----------------------------- | --------------- |
| LOOKUP_TYPE     | LOOKUP_CODE | MEANING                      | DESCRIPTION                                                                                        | ENABLED_FLAG | START_DATE_ACTIVE             | END_DATE_ACTIVE |
| WSH_PICK_STATUS | B           | Backordered                  | Shipments with backordered status, which lines failed to be allocated in inventory.                | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | C           | Shipped                      |                                                                                                    | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | D           | Canceled                     |                                                                                                    | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | I           | Interfaced                   | Shipments with interfaced status, which lines were shipped and interfaced to orders and inventory. | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | N           | Not shipped                  |                                                                                                    | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | P           | Pending inventory processing | Processing of inventory transactions is pending for the shipment line.                             | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | R           | Ready to release             | Shipments with ready to release status, which lines are ready to be released.                      | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | S           | Released to warehouse        | Shipments with released to warehouse status.                                                       | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | X           | Not applicable               | Shipments with not applicable status, which lines are not applicable for pick release.             | Y            | 1959-01-01T00:00:00.000+00:00 |                 |
| WSH_PICK_STATUS | Y           | Staged                       | Shipments with staged status, which lines were picked and staged by inventory.                     | Y            | 1959-01-01T00:00:00.000+00:00 |                 |

## Query to get Style
```
# STYLE?
SELECT 
    style_item.item_number AS style_item_number,
    style_item.inventory_item_id,
    esitl.description AS current_bad_value,
    style_flex.attribute_char1 AS correct_flexfield_value
FROM 
    egp_system_items_b style_item,
    egp_system_items_tl esitl,
    ego_item_eff_b style_flex
WHERE 
    style_item.inventory_item_id = esitl.inventory_item_id
    AND style_item.organization_id = esitl.organization_id
    AND esitl.language = 'US'
    AND style_item.inventory_item_id = style_flex.inventory_item_id
    AND style_item.master_org_id = style_flex.organization_id
    AND style_flex.context_code = 'All Items Attributes Style'
    AND style_flex.ACD_TYPE = 'PROD'
    AND esitl.description != style_flex.attribute_char1
    AND style_flex.attribute_char1 IS NOT NULL
    AND UPPER(esitl.description) LIKE 'SP%'
    AND style_item.template_item_flag = 'N'  -- EXCLUDE templates!
    AND ROWNUM = 1;

# MIGHT SELECT A TEMPLATE (style_item.template_item_flag 'Y')
SELECT 
    style_item.item_number AS style_item_number,
    esitl.description AS current_bad_value,
    style_flex.attribute_char1 AS correct_flexfield_value
FROM 
    egp_system_items_b style_item,
    egp_system_items_tl esitl,
    ego_item_eff_b style_flex
WHERE 
    style_item.inventory_item_id = esitl.inventory_item_id
    AND style_item.organization_id = esitl.organization_id
    AND esitl.language = 'US'
    AND style_item.inventory_item_id = style_flex.inventory_item_id
    AND style_item.master_org_id = style_flex.organization_id
    AND style_flex.context_code = 'All Items Attributes Style'
    AND style_flex.ACD_TYPE = 'PROD'
    AND esitl.description != style_flex.attribute_char1
    AND style_flex.attribute_char1 IS NOT NULL
    AND UPPER(esitl.description) LIKE 'SP%'
    AND ROWNUM = 1;
```

## Query to get SKU from STYLE
 ```
 SELECT 
    sku.item_number AS sku_number,
    sku.inventory_item_id AS sku_id
FROM 
    egp_system_items_b sku
WHERE 
    sku.style_item_id = 300000418449227  -- Your Style's inventory_item_id
    AND ROWNUM = 1;
 ```
