# QUERY

```sql
/*
 * AP-I-3006 - Initiate B2C Customer Refund in Payment Services
 * Mapping: docs/AP-I-3006/AP-I-3006 - Initiate B2C Customer Refund in Payment Services.xlsx - Mapping.csv
 *
 * Open TODOs (assumptions not stated in the mapping — validate in evdi-test before production):
 *   1. AR-to-AP link: application_ref_num = invoice_num (+ org_id). Alternative may be application_ref_id = invoice_id.
 *   2. ra.status = 'APP': common AR "applied" filter; not in AP-I-3006 spec (also not used in AP-I-3004).
 *   3. Credit memo receipt method: mapping calls for Non Insurance method on the *original* sales order for exchange
 *      orders; query uses ct_reference -> remit_orig.invoice_reference directly.
 *   4. api.approval_status = 'APPROVED': used in AP-I-3004 (WP_AP_INVOICE_HOLDS_DM) but not in AP-I-3006 mapping.
 *
 * Related integration for AP-side "not paid" pattern: AP-I-3004 / WP_AP_INVOICE_HOLDS_DM.sql
 *   (queries ap_invoices_all only: PAYMENT REQUEST, SOURCE = Receivables, PAYMENT_STATUS_FLAG = 'N').
 */
WITH eligible_receipt_methods AS (
    /* Mapping: receipt method must be one of the four Stripe/PayPal/Affirm methods below. */
    SELECT
        receipt_method_id,
        name
    FROM ar_receipt_methods
    WHERE name IN (
        'CHASUS-0257-Stripe',
        'ROYCCA-2198-Stripe',
        'CHASUS-0257-PayPal',
        'CHASUS-0257-Affirm'
    )
),
/*
 * Base refund set: AR refund requests that are unpaid in AP and within the extract window.
 *
 * From mapping (extraction criteria):
 *   - application_ref_type = 'AP_REFUND_REQUEST' on ar_receivable_applications_all
 *   - Payment status: not paid in Accounts Payable
 *   - Source: Receivables
 *
 * AP join rationale:
 *   Mapping requires "Not Paid Status in Accounts Payable Module". AR alone cannot express that;
 *   ap_invoices_all enforces an unpaid Receivables-sourced payment request (same intent as AP-I-3004).
 *
 * TODO — join keys (reasonable guess, not in mapping):
 *   api.invoice_num = ra.application_ref_num  — assumed because application_ref_num is the refund/AP doc
 *   reference and is mapped to output Refund Number; confirm against sample rows in evdi-test.
 *   api.org_id = ra.org_id                      — assumed to scope AR application and AP invoice to same BU.
 *   If validation fails, try: ra.application_ref_id = api.invoice_id
 *
 * TODO — ra.status = 'APP' (reasonable guess, not in mapping):
 *   Limits to active/applied receivable applications. Remove or adjust if it excludes valid refunds.
 *
 * Parameters (report convention, aligned with other WP integration extracts):
 *   Date range on ra.apply_date, or P_TRANSACTION_NUMBERS matching receipt_number / trx_number.
 *   If both date params are null and P_TRANSACTION_NUMBERS is empty, no rows are returned.
 */
unpaid_ap_refunds AS (
    SELECT
        ra.receivable_application_id,
        ra.amount_applied,
        ra.application_ref_num,
        ra.apply_date,
        ra.cash_receipt_id,
        ra.customer_trx_id,
        ra.org_id
    FROM ar_receivable_applications_all ra
    INNER JOIN ap_invoices_all api
        ON api.invoice_num = ra.application_ref_num /* TODO: validate link — see block comment above */
        AND api.org_id = ra.org_id                   /* TODO: validate link — see block comment above */
    WHERE ra.application_ref_type = 'AP_REFUND_REQUEST' /* Mapping */
        AND ra.status = 'APP'                            /* TODO: not in mapping — validate or remove */
        AND api.invoice_type_lookup_code = 'PAYMENT REQUEST' /* AP-side: Receivables refund payment request */
        AND api.source = 'Receivables'                     /* Mapping */
        AND api.payment_status_flag = 'N'                  /* Mapping: not paid in AP */
        AND (
            (
                :P_FROM_DATE IS NOT NULL
                AND :P_TO_DATE IS NOT NULL
                AND ra.apply_date >= CAST(:P_FROM_DATE AS DATE)
                AND ra.apply_date <= CAST(:P_TO_DATE AS DATE)
            )
            OR EXISTS (
                SELECT 1
                FROM ar_cash_receipts_all cr
                WHERE cr.cash_receipt_id = ra.cash_receipt_id
                    AND cr.receipt_number IN (:P_TRANSACTION_NUMBERS)
            )
            OR EXISTS (
                SELECT 1
                FROM ra_customer_trx_all cm
                WHERE cm.customer_trx_id = ra.customer_trx_id
                    AND cm.org_id = ra.org_id
                    AND cm.trx_number IN (:P_TRANSACTION_NUMBERS)
            )
        )
),
/* Mapping: receipt path — ar_cash_receipts_all joined to eligible receipt methods and remit refs. */
receipt_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        remit.invoice_reference AS sales_order_number,
        cr.receipt_number AS transaction_number,
        rm.name AS transaction_type,
        cr.receipt_date AS transaction_date,
        cr.amount AS transaction_amount,
        cr.currency_code AS currency,
        uf.amount_applied AS refund_amount,
        uf.application_ref_num AS refund_number,
        uf.apply_date AS refund_date,
        CASE
            WHEN cr.attribute_category = 'Non Insurance' THEN cr.attribute1
        END AS sales_order_payment_id
    FROM unpaid_ap_refunds uf
    INNER JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = uf.cash_receipt_id
    INNER JOIN eligible_receipt_methods rm
        ON rm.receipt_method_id = cr.receipt_method_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cr.org_id
    LEFT JOIN ar_cash_remit_refs_all remit
        ON remit.cash_receipt_id = cr.cash_receipt_id
    WHERE uf.cash_receipt_id IS NOT NULL
),
/*
 * Mapping: credit memo path — ra_customer_trx_all + sum of ra_customer_trx_lines_all (correlated SUM per row).
 * TODO: exchange orders — mapping says derive Non Insurance receipt method from original sales order tied to
 *       the exchange order; transaction_type subquery uses cm.ct_reference -> remit_orig.invoice_reference.
 */
credit_memo_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        cm.ct_reference AS sales_order_number,
        cm.trx_number AS transaction_number,
        (
            SELECT rm_orig.name
            FROM ar_cash_receipts_all cr_orig
            INNER JOIN ar_cash_remit_refs_all remit_orig
                ON remit_orig.cash_receipt_id = cr_orig.cash_receipt_id
            INNER JOIN eligible_receipt_methods rm_orig
                ON rm_orig.receipt_method_id = cr_orig.receipt_method_id
            WHERE cr_orig.attribute_category = 'Non Insurance'
                AND remit_orig.invoice_reference = cm.ct_reference
            FETCH FIRST 1 ROW ONLY
        ) AS transaction_type,
        cm.trx_date AS transaction_date,
        (
            SELECT SUM(l.extended_amount)
            FROM ra_customer_trx_lines_all l
            WHERE l.customer_trx_id = cm.customer_trx_id
                AND l.org_id = cm.org_id
        ) AS transaction_amount,
        cm.invoice_currency_code AS currency,
        uf.amount_applied AS refund_amount,
        uf.application_ref_num AS refund_number,
        uf.apply_date AS refund_date,
        CAST(NULL AS VARCHAR2(150)) AS sales_order_payment_id
    FROM unpaid_ap_refunds uf
    INNER JOIN ra_customer_trx_all cm
        ON cm.customer_trx_id = uf.customer_trx_id
        AND cm.org_id = uf.org_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cm.org_id
    WHERE uf.customer_trx_id IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM ar_cash_receipts_all cr_orig
            INNER JOIN ar_cash_remit_refs_all remit_orig
                ON remit_orig.cash_receipt_id = cr_orig.cash_receipt_id
            INNER JOIN eligible_receipt_methods rm_orig
                ON rm_orig.receipt_method_id = cr_orig.receipt_method_id
            WHERE cr_orig.attribute_category = 'Non Insurance'
                AND remit_orig.invoice_reference = cm.ct_reference
        )
)
SELECT
    business_unit,
    sales_order_number,
    transaction_number,
    transaction_type,
    transaction_date,
    transaction_amount,
    currency,
    refund_amount,
    refund_number,
    refund_date,
    sales_order_payment_id
FROM (
    SELECT * FROM receipt_refunds
    UNION ALL
    SELECT * FROM credit_memo_refunds
)

```