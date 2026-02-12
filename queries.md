
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
