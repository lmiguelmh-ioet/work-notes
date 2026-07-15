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
   AND sdl.doc_line_id_int_2 = CASE
       WHEN fl.fulfill_line_number != TRUNC(fl.fulfill_line_number)
           THEN fl.fulfill_line_number ELSE l.line_number END
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
   AND sdl.doc_line_id_int_2 = CASE
       WHEN fl.fulfill_line_number != TRUNC(fl.fulfill_line_number)
           THEN fl.fulfill_line_number ELSE l.line_number END
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
   AND sdl.doc_line_id_int_2 = CASE
       WHEN fl.fulfill_line_number != TRUNC(fl.fulfill_line_number)
           THEN fl.fulfill_line_number ELSE l.line_number END
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
   AND sdl.doc_line_id_int_2 = CASE
       WHEN fl.fulfill_line_number != TRUNC(fl.fulfill_line_number)
           THEN fl.fulfill_line_number ELSE l.line_number END
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
```