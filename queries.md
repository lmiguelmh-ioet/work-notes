
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
