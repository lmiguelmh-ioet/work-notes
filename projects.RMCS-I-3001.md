
## Query for getting Validate Customer Contract results

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