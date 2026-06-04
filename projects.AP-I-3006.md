# QUERY

## V4 Questions

### Prompt

```
As a Oracle ERP expert and senior data analyst:

Create the query for this and put it in: BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/
WP_AP_B2C_CUSTOMER_REFUND_DM.sql

@docs/AP-I-3006/AP-I-3006 - Initiate B2C Customer Refund in Payment Services.xlsx - Mapping.csv

Follow closely the mapping, and produce a simple straigthforward query preferring readability.

As you followed closely the mapping, surely you notice issues or  problems or observations or any other thing, please annotate it in the same line with a comment, and make a summary with all the questions / observations you've found.

As a hint you may use this structure:
WITH eligible_receipt_methods AS (..)
unpaid_ap_refunds AS (..)
receipt_refunds AS (..)
credit_memo_refunds AS (..)
select... union ...
```

1. OK ~~Table name in mapping — CSV says `ar_receivable_applications_all`; standard Fusion name is `AR_RECEIVABLE_APPLICATIONS_ALL` (same name, different casing). Confirm no view/synonym difference in your BI data source.~~
    
2. AR ↔ AP link — Join is `application_ref_id = ap_invoices_all.invoice_id` for `AP_REFUND_REQUEST`. Alternative links exist (`application_ref_num = invoice_num`, `reference_key1 = receivable_application_id` on AP). Confirm which is authoritative in your environment.
    
3. REMOVED FROM QUERY ~~`status = 'APP'` — Not in the mapping; added to skip reversed/unapplied rows (same idea as `WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM`). Confirm if `UNAPP` or other statuses should be included.~~ 
    
4. `applied_payment_schedule_id = -8` — Common for AR refunds in Fusion but not in the mapping. Confirm whether this filter is required.
    
5. Refund amount sign — `amount_applied` may be negative on refund applications. Confirm whether Payment Services expects signed values or `ABS(amount_applied)`.
    
6. Currency (receipt path) — Mapping points to `ar_cash_receipts_all` but does not name a column; query uses `currency_code`. Confirm column name.
    
7. Currency (credit memo path) — Mapping has no CM currency; query uses `invoice_currency_code`. Confirm.
    
8. Transaction amount (CM) — Line `extended_amount` sums are often negative for credit memos. Confirm if outbound amount should be `ABS(SUM(...))`.
    
9. Refund number — Mapping says `Application_Ref_Num` but also “use `receipt_id` / `customer_trx_id` to derive.” Clarify whether outbound refund number is `application_ref_num`, receipt number, trx number, or AP invoice number.
    
10. Sales order payment ID — Only defined for receipts (`attribute_category = 'Non Insurance'`, `attribute1`). CM branch returns `NULL`. Confirm if CM refunds need payment ID from another source.
    
11. Sales order number (receipts) — `ar_cash_remit_refs_all` can have multiple rows per receipt → possible duplicate output rows. Confirm 1:1 rule or dedupe logic.
    
12. Sales order number (CM) — exchange orders — Mapping row 17: derive non-insurance receipt method from original sales order on exchange orders. Not implemented; needs business rules (likely `doo_headers_all` / original order linkage).
    
13. Transaction type (CM) — Mapping lists `ar_cash_receipts_all.receipt_method_id` even for credit memos. Query requires a linked `cash_receipt_id` on the application so receipt-method criteria apply. CM refunds without a linked receipt are excluded — confirm that is correct.
    
14. FIXED ~~Receipt method table — Uses `ar_receipt_methods_vl`. Confirm name matches production (vs `_b` + language table).~~
    
15. SAME AS OTHER QUERIES ~~Business unit — Uses `fun_all_business_units_v` (consistent with other FIN DMs). Mapping only says “derive BU name from `org_id`.”~~
    
16. No date / incremental parameters — Mapping has no `P_FROM_DATE` / `P_TO_DATE`; unlike `WP_AP_INVOICE_HOLDS_DM` and SCM refund report. Confirm if BI report parameters should be added.
    
17. Cancelled AP invoices — `unpaid_ap_refunds` does not exclude `cancelled_date IS NOT NULL`. Confirm if cancelled payment requests should be excluded.
    
18. ~~`fusion.` schema prefix — Some DMs use `fusion.` prefix, others do not. This query follows the unprefixed style of `WP_AP_INVOICE_HOLDS_DM` / `WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM`. Match your BI Publisher data source connection.~~

---

1. Refund application status — Mapping says “Refund” / `AP_REFUND_REQUEST` but not which `status` value. Production data uses `ACTIVITY`, not `APP`. Using `APP` returns zero rows.
    
2. `applied_payment_schedule_id = -8` — Not in the mapping; it is Oracle’s seeded refund application schedule. Needed to isolate refund rows and avoid standard receipt-to-invoice applications.
    
3. `amount_applied > 0` — Oracle creates offsetting pairs (+/−) for the same refund. Mapping does not mention this; filter keeps one row per refund.
    
4. AR ↔ AP join key — Unpaid AP filter joins on `application_ref_id = invoice_id` (+ `org_id`). Mapping text “use receipt_id / customer_trx_id to derive refund number” refers to `application_ref_num`, not the join key.
    
5. `application_ref_num` vs receipt/CM id — Mapping is ambiguous whether `refund_number` is `application_ref_num` as stored or a lookup from `cash_receipt_id` / `customer_trx_id`. Query outputs `application_ref_num` as mapped.
    
6. AP “not paid” definition — Implemented as `payment_status_flag = 'N'` on `ap_invoices_all`. Not spelled out in the mapping. `WP_AP_INVOICE_HOLDS_DM` also requires `APPROVAL_STATUS = 'APPROVED'` — should that be added?
    
7. `invoice_type_lookup_code` spelling — Uses `'PAYMENT REQUEST'` (space), consistent with holds DM; other repo SQL uses `'PAYMENT_REQUEST'`.
    
8. Currency (CM path) — Spreadsheet only names currency on the receipt row; CM uses `invoice_currency_code`.
    
9. Transaction amount (receipt) — Mapping uses full `cr.amount`, not remaining/unapplied balance — confirm for partial refunds.
    
10. CM line amounts — `SUM(extended_amount)` without `ABS`; sign convention not specified in mapping.
    
11. Sales order on CM — Mapping column is `ct_reference`, but in practice that is often an AR internal link to the related invoice, not the DOO order on `ar_cash_remit_refs_all.invoice_reference`.
    
12. CM transaction type — Mapping points at `ar_cash_receipts_all` / receipt method; implemented via `cm_original_receipt_methods` (invoice → cash receipt → allowed method). Exchange orders may still need extra paths if none of the invoice links resolve.
    
13. Sales order payment ID — Only on receipt path (`attribute_category = 'Non Insurance'`, `attribute1`). Null on CM by design. Confirm literal category spelling/casing in flexfields.
    
14. Receipt method allow list — Hardcoded names; may need `ar_receipt_methods_vl` if names differ by language.
    
15. Insurance receipts — e.g. `CHASUS-0257-Insurance` are correctly excluded (not in mapping list).
    
16. Date / list parameters — `:P_FROM_DATE`, `:P_TO_DATE`, `:P_RECEIPT_NUMBERS`, `:P_CREDIT_MEMO_NUMBERS`, `:P_REFUND_NUMBERS` are not in the mapping; follow other FIN DMs. Filter on `apply_date`, not receipt/CM creation date.
    
17. BI Publisher bind lists — `IN (:P_…)` with all parameters null can fail; OIC should always pass a date range or explicit numbers.
    
18. Output grain — One row per `receivable_application_id`; confirm whether OIC should de-duplicate if multiple rows per refund are possible.
    
19. Extra CTE `refund_applications` — Not in your hint structure but keeps AR+AP filters in one place for both union branches.
## V3 Questions

### Assumptions not spelled out in the mapping

|Topic|What we did|Question|
|---|---|---|
|AP “not paid”|`ap_invoices_all.payment_status_flag = 'N'`, `source = 'Receivables'`, `invoice_type_lookup_code = 'PAYMENT REQUEST'`|Mapping does not name table/columns. Is this the right “not paid” definition, or should we use `IBY_PAYMENTS_ALL.payment_status` / payment history?|
|AR → AP link|`application_ref_id = ap_invoices_all.invoice_id`|Not documented in mapping. Needs UAT confirmation for `AP_REFUND_REQUEST`.|
|Application status|`app.status = 'APP'`|Not in mapping. Should `UNAPP` / reversal rows be excluded?|
|Receipt vs CM split|Receipt: `cash_receipt_id IS NOT NULL`; CM: `customer_trx_id IS NOT NULL AND cash_receipt_id IS NULL`|Mapping does not define two paths. What if both IDs are set?|

### Field-level gaps

|Field|Observation|
|---|---|
|Currency|Spreadsheet has no CM column; receipt column has no field name. We used `currency_code` / `invoice_currency_code`.|
|Refund number|Mapping says `Application_Ref_Num` and “use receipt_id / customer_trx_id to derive.” Unclear if that means join logic vs displaying `application_ref_num` as-is.|
|Transaction amount (receipt)|Mapping uses full `amount` on the receipt, not remaining/unapplied amount. OK for full refunds; unclear for partial.|
|Transaction amount (CM)|Sum of `extended_amount`; sign not specified (CM lines often negative).|
|Sales order payment ID|Only on receipt path (`attribute_category = 'Non Insurance'`, `attribute1`). CM correctly null. Confirm exact category literal in prod.|
|Business unit|“Derive from org_id.” We use `fun_all_business_units_v`; other reports use `hr_organization_units`.|

### Credit memo / exchange-order logic

|Topic|Risk|
|---|---|
|Transaction type on CM|Mapping points at `ar_cash_receipts_all` / `receipt_method_id` for both paths. We resolve method via `order_receipt_method` on `ct_reference`.|
|Exchange orders|Mapping note (col 5): for exchange, use original sales order’s non-insurance receipt method. We join on `cm.ct_reference` only—exchange CMs may drop out or get the wrong method unless DOO/original-order logic is added.|
|CM sales order|We use `ct_reference` as sales order number; the exchange note applies to receipt method, not this field.|

### Data quality / grain

|Topic|Observation|
|---|---|
|Multiple remit refs|`MAX(invoice_reference)` per receipt is arbitrary if several sales orders are on one receipt.|
|Row grain|One row per `ar_receivable_applications_all` row; Oracle can create multiple `APP`/`UNAPP` rows per refund. Confirm expected grain for OIC.|
|Receipt method list|Hardcoded four names; may drift vs setup; consider `_VL` if names are translated.|

### Filters not in the mapping

|Item|Note|
|---|---|
|Date parameters|`:P_FROM_DATE` / `:P_TO_DATE` on `apply_date`—not in mapping. Alternative: `receipt_date`, `trx_date`, AP `creation_date`.|
|List parameters|`:P_RECEIPT_NUMBERS`, `:P_CREDIT_MEMO_NUMBERS`, `:P_REFUND_NUMBERS`—convention from other FIN reports; empty `IN (...)` can break BI Publisher if OIC does not always pass binds.|
|Approval status|`WP_AP_INVOICE_HOLDS_DM` also uses `APPROVAL_STATUS = 'APPROVED'`. Mapping does not; may include unapproved payment requests.|

### Repo / technical consistency

|Topic|Note|
|---|---|
|`PAYMENT REQUEST` vs `PAYMENT_REQUEST`|Mixed usage across FIN reports; validate which value exists in your pod.|

---

Highest-impact items to confirm with functional/QA before production:

1. Exchange orders — original SO receipt method vs `ct_reference` only.
2. Refund number — `application_ref_num` vs derivation via `cash_receipt_id` / `customer_trx_id`.
3. AP not paid — `payment_status_flag` on payment request invoice vs payment/disbursement tables.
4. Whether `APPROVAL_STATUS = 'APPROVED'` should be required.
5. CM transaction amount sign and receipt path amount semantics for partial refunds.

## PROMPT
```
As a Oracle ERP expert and senior data analyst:

Create the query for this and put it in: BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/
WP_AP_B2C_CUSTOMER_REFUND_DM.sql

@docs/AP-I-3006/AP-I-3006 - Initiate B2C Customer Refund in Payment Services.xlsx - Mapping.csv 

These are involved tables:

AR_RECEIVABLE_APPLICATIONS_ALL
The AR_RECEIVABLE_APPLICATIONS_ALL table stores all accounting entries for both your cash and credit memo applications. The APPLICATION_TYPE column stores either CASH or CM (for credit memo applications). Each row in this table includes the amount applied, status, and accounting flexfield information. Possible application statuses include: APP for applied, UNAPP for unapplied, ACC for on-account, UNID for unidentified, ACTIVITY for receivable activity, and OTHER ACC for other receipt application. Receivables looks at  application status to determine which flexfield account to use. Receivables uses CODE_COMBINATION_ID foreign key column to associate payment with the unidentified flexfield account. The CODE_COMBINATION_ID column stores valid Accounting Flexfield segment value combinations credited in General Ledger when this application is posted. Cash applications represent cash receipt applications. The sum of AMOUNT_APPLIED column for cash applications should always equal the amount of the cash receipt. A negative value in AMOUNT_APPLIED column becomes a debit when application is posted to General Ledger. When a cash receipt is initially created, Receivables creates a row in this table for cash receipt amount with status of UNAPP. For each subsequent application, Receivables creates two rows: one row with status of APP for amount applied to invoice, and one row with status UNAPP for the negative of the applied amount. If you reverse a cash application, Receivables creates two new rows: one row with status APP for the inverse amount of the original application (negative of the original application amount), and one row with status UNAPP for positive amount of application that is reversed. Credit memo applications do not have rows with status UNAPP, and use only rows with status of APP. The CASH_RECEIPT_ID column stores ID of the receipt you entered. Receivables concurrently creates a record for this receipt in AR_CASH_RECEIPTS_ALL table. This column is null for credit memo application. The CUSTOMER_TRX_ID and PAYMENT_SCHEDULE_ID columns also identify transaction you are applying. The APPLIED_CUSTOMER_TRX_ID and APPLIED_PAYMENT_SCHEDULE_ID columns identify invoice or credit memo that receives the application. If you apply a credit memo against the invoice, Receivables creates a record in this table. The CUSTOMER_TRX_ID and PAYMENT_SCHEDULE_ID columns for this record identify the credit memo you are applying. The APPLIED_CUSTOMER_TRX_ID and APPLIED_PAYMENT_SCHEDULE_ID columns for this record belong to invoice being applied. If you combine an on-account credit and a receipt, Receivables creates a record in this table. The CASH_RECEIPT_ID and PAYMENT_SCHEDULE_ID columns for this record identify the receipt. The APPLIED_CUSTOMER_TRX_ID and APPLIED_PAYMENT_SCHEDULE_ID columns for this record identify the on-account credit you combine with the receipt. The CONFIRMED_FLAG column is a denormalization from the AR_CASH_RECEIPTS_ALL table. If the cash receipt is not confirmed, applications of that receipt are not reflected in the payment schedule of the transaction the receipt is applied against.

AP_INVOICES_ALL
AP_INVOICES_ALL contains records for invoices you enter.  There is one row for each invoice youenter.  An invoice can have one or more invoice distribution lines.  An invoice can also have one or more scheduled payments.   
An invoice of type EXPENSE REPORT must relate to a row in AP_EXPENSE_REPORT_HEADERS_ALL unless the record has been purged from AP_EXPENSE_REPORT_HEADERS_ALL.  Your Oracle Payables application uses the INTEREST type invoice for interest that it calculates on invoices that are overdue.  
Your Oracle Payables application links the interest invoice to the original invoice by inserting the INVOICE_ID  in the AP_INVOICE_RELATIONSHIPS table. This table corresponds to the Invoices window.

AR_CASH_RECEIPTS_ALL
The AR_CASH_RECEIPTS_ALL table stores one record for each receipt that you enter. Oracle Receivables concurrently creates records in the AR_CASH_RECEIPT_HISTORY_ALL, AR_PAYMENT_SCHEDULES_ALL, and AR_RECEIVABLE_APPLICATIONS_ALL tables for invoice-related receipts. For receipts that are not related to invoices, such as miscellaneous receipts, Receivables creates records in the AR_MISC_CASH_DISTRIBUTIONS_ALL table instead of the AR_RECEIVABLE_APPLICATIONS_ALL table. Receivables associates a status with each receipt. These statuses include: APP for applied, UNAPP for unapplied, UNID for unidentified, NSF for nonsufficient funds, REV for reversed receipt and STOP for stop payment. Receivables does not update the status of a receipt from UNAPP to APP until the entire amount of the receipt is either applied or placed on account. A receipt can have a status of APP even if the entire receipt amount is placed on account. Cash receipts proceed through the confirmation, remittance, and clearance steps. Each step creates rows in the AR_CASH_RECEIPT_HISTORY table. The CODE_COMBINATION_ID column in this table stores the general ledger accounts that are debited and credited as part of the cycle of steps. The RECEIVABLES_TRX_ID column links the AR_CASH_RECEIPTS_ALL table to  AR_RECEIVABLES_TRX_ALL table and identifies receivables activity associated with miscellaneous receipts. The DISTRIBUTION_SET_ID column links AR_CASH_RECEIPTS_ALL table to AR_DISTRIBUTION_SETS_ALL table and identifies  distribution set and distribution set line accounts that are credited for miscellaneous receipts. The CUSTOMER_BANK_ACCOUNT_ID column is a foreign key to the IBY_EXT_BANK_ACCOUNTS table for bank accounts that do not belong to you and have a type of EXTERNAL.  The primary key for this table is CASH_RECEIPT_ID.

AR_CASH_REMIT_REFS_ALL
This table stores the references on a receipt

RA_CUSTOMER_TRX_ALL
This table contains invoice, debit memo, bills receivable, and credit memo header information. Each row in this table includes general invoice information such as customer, transaction type, and printing instructions. One row exists for each invoice, debit memo, bill receivable, and credit memo. Invoices, debit memos, credit memos, and bills receivable are distinguished by their associated transaction types stored in the this table.

RA_CUSTOMER_TRX_LINES_ALL
The RA_CUSTOMER_TRX_LINES_ALL table stores line information about invoices, debit memos, credit memos, and bills receivable. For example, an invoice can have one line for Product A and another line for Product B. Each line requires one row in this table.
Invoices, debit memos, credit memos, and bills receivable distinguished by the transaction type of the corresponding row in the RA_CUSTOMER_TRX_ALL table. Credit memos must also have a value in the PREVIOUS_CUSTOMER_TRX_LINE_ID column. On-account credits, which are not related to specific invoices or invoice lines when they are created, will not have values in this column.
The QUANTITY_ORDERED column stores the amount of product that was ordered. The QUANTITY_INVOICED column stores the amount of product that was invoiced. For manually entered invoices, the QUANTITY_ORDERED and QUANTITY_INVOICED columns must be the same. For invoices that were imported through AutoInvoice, the QUANTITY_ORDERED and QUANTITY_INVOICED columns can be different. If you enter a credit memo, the QUANTITY_CREDITED column stores the amount of product that was credited.
The UOM_CODE column stores the unit of measure code as defined in the INV_UNITS_OF_MEASURE table. The UNIT_STANDARD_PRICE column stores the list price per unit for this transaction line. The UNIT_SELLING_PRICE column stores the selling price per unit for this transaction line. For transactions that were imported through AutoInvoice, the UNIT_STANDARD_PRICE and UNIT_SELLING_PRICE columns can be different. The DESCRIPTION, TAXING_RULE, QUANTITY_ORDERED, UNIT_STANDARD_PRICE, UOM_CODE, and UNIT_SELLING_PRICE columns are required even though they are null allowed.
Receivables uses the LINE_TYPE column to distinguish between the different types of lines. LINE represents regular invoice lines that normally refer to an item. TAX represents a tax line. The LINK_TO_CUST_TRX_LINE_ID column references the invoice line that is associated with the row that holds the TAX line type. FREIGHT is similar to TAX, but you can have at most one freight line per invoice line. You can also have one freight line that has a null LINK_TO_CUST_TRX_LINE_ID column. An invoice that has one freight line with a null LINK_TO_CUST_TRX_LINE_ID column has header-level freight.
CB represents a chargeback line. For every row in this table that belongs to a completed postable or nonpostable transaction, where the RA_CUSTOMER_TRX.COMPLETE_FLAG is Y, there must be at least one row in the RA_CUST_TRX_LINE_GL_DIST table that stores accounting information. There must be at least one row in this table even for nonpostable transactions.
The primary key for this table is CUSTOMER_TRX_LINE_ID.

If you have any question or doubt or assumption about anything (including columns, ways to join tables), just tell me.

```

## V4.1 - with -8 and distinct - as per Vijay

```
```


## V4 - being validated - simplest!

```sql
/*
  AP-I-3006 - Initiate B2C Customer Refund in Payment Services
  Mapping: docs/AP-I-3006/AP-I-3006 - Initiate B2C Customer Refund in Payment Services.xlsx - Mapping.csv
*/
WITH eligible_receipt_methods AS (
    SELECT
        rm.receipt_method_id,
        rm.name AS receipt_method_name
    FROM ar_receipt_methods rm
    WHERE rm.name IN (
        'CHASUS-0257-Stripe',
        'ROYCCA-2198-Stripe',
        'CHASUS-0257-PayPal',
        'CHASUS-0257-Affirm'
    )
),
receipt_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        rem.invoice_reference AS sales_order_number,            -- ar_cash_remit_refs_all; multiple remit rows may duplicate
        cr.receipt_number AS transaction_number,
        erm.receipt_method_name AS transaction_type,
        cr.receipt_date AS transaction_date,
        cr.amount AS transaction_amount,
        cr.currency_code AS currency,
        app.amount_applied AS refund_amount,                    -- confirm sign (refund rows may be negative)
        app.application_ref_num AS refund_number,               -- mapping also says "use receipt_id to derive" — confirm meaning
        app.apply_date AS refund_date,
        CASE
            WHEN cr.attribute_category = 'Non Insurance'
            THEN cr.attribute1
        END AS sales_order_payment_id
    FROM ar_receivable_applications_all app
    INNER JOIN ap_invoices_all aia
        ON aia.invoice_id = app.application_ref_id              -- confirm APPLICATION_REF_ID vs invoice_num / reference_key1
        AND aia.invoice_type_lookup_code = 'PAYMENT REQUEST'
        AND aia.source = 'Receivables'
        AND aia.payment_status_flag = 'N'
    INNER JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = app.cash_receipt_id
    INNER JOIN eligible_receipt_methods erm
        ON erm.receipt_method_id = cr.receipt_method_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cr.org_id
    LEFT JOIN ar_cash_remit_refs_all rem
        ON rem.cash_receipt_id = cr.cash_receipt_id
    WHERE app.application_ref_type = 'AP_REFUND_REQUEST'
      AND app.application_type = 'CASH'                         -- added for clear intent
),
credit_memo_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        cm.ct_reference AS sales_order_number,                  -- exchange-order / non-insurance method not implemented
        cm.trx_number AS transaction_number,
        erm.receipt_method_name AS transaction_type,
        cm.trx_date AS transaction_date,
        (
            SELECT SUM(ctl.extended_amount)
            FROM ra_customer_trx_lines_all ctl
            WHERE ctl.customer_trx_id = cm.customer_trx_id
              AND ctl.org_id = cm.org_id
        ) AS transaction_amount,                                -- SUM(extended_amount); CM totals often negative
        cm.invoice_currency_code AS currency,
        app.amount_applied AS refund_amount,
        app.application_ref_num AS refund_number,
        app.apply_date AS refund_date,
        NULL AS sales_order_payment_id
    FROM ar_receivable_applications_all app
    INNER JOIN ap_invoices_all aia
        ON aia.invoice_id = app.application_ref_id              -- confirm APPLICATION_REF_ID vs invoice_num / reference_key1
        AND aia.invoice_type_lookup_code = 'PAYMENT REQUEST'
        AND aia.source = 'Receivables'
        AND aia.payment_status_flag = 'N'
    INNER JOIN ra_customer_trx_all cm
        ON cm.customer_trx_id = app.customer_trx_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cm.org_id
    INNER JOIN eligible_receipt_methods erm
        ON erm.receipt_method_id = cm.receipt_method_id
    WHERE app.application_ref_type = 'AP_REFUND_REQUEST'
      AND app.application_type = 'CM'                           -- added for clear intent
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
FROM receipt_refunds
UNION ALL
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
FROM credit_memo_refunds
```


## V3 - not validated - complicated
```sql
-- AP-I-3006: Initiate B2C Customer Refund in Payment Services
-- Source: Receivables refunds (AP_REFUND_REQUEST) with AP payment request not yet paid.

WITH allowed_receipt_methods AS (
    SELECT name
    FROM ar_receipt_methods -- mapping: receipt method names; hardcoded list may drift from prod setup / use _VL if translated names differ
    WHERE name IN (
        'CHASUS-0257-Stripe',
        'ROYCCA-2198-Stripe',
        'CHASUS-0257-PayPal',
        'CHASUS-0257-Affirm'
    )
),
cm_amounts AS (
    SELECT
        customer_trx_id,
        org_id,
        SUM(extended_amount) AS transaction_amount -- mapping: sum line extended_amounts; sign not specified (CM lines often negative—confirm downstream expects signed vs ABS)
    FROM ra_customer_trx_lines_all
    GROUP BY customer_trx_id, org_id
),
receipt_sales_orders AS (
    SELECT
        remit.cash_receipt_id,
        MAX(remit.invoice_reference) AS sales_order_number -- mapping: invoice_reference; MAX arbitrary when multiple remit refs per receipt—confirm business rule
    FROM ar_cash_remit_refs_all remit
    GROUP BY remit.cash_receipt_id
),
order_receipt_method AS (
    SELECT
        remit.invoice_reference AS sales_order_number,
        MAX(rm.name) AS receipt_method_name -- mapping CM note: for exchange orders, method should come from original SO, not exchange—ct_reference-only join may miss those rows
    FROM ar_cash_remit_refs_all remit
    JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = remit.cash_receipt_id
    JOIN ar_receipt_methods rm
        ON rm.receipt_method_id = cr.receipt_method_id
    JOIN allowed_receipt_methods arm
        ON arm.name = rm.name
    GROUP BY remit.invoice_reference
),
unpaid_ap_refund AS (
    SELECT invoice_id
    FROM ap_invoices_all
    WHERE invoice_type_lookup_code = 'PAYMENT REQUEST' -- mapping: "not paid in AP"; table/column not specified—aligned with WP_AP_INVOICE_HOLDS_DM ('PAYMENT REQUEST' vs 'PAYMENT_REQUEST' varies elsewhere in repo)
      AND source = 'Receivables' -- mapping extraction criterion "Source: Receivables"
      AND payment_status_flag = 'N' -- mapping: not paid; confirm vs IBY_PAYMENTS_ALL.payment_status if disbursement already initiated
      -- observation: WP_AP_INVOICE_HOLDS_DM also filters APPROVAL_STATUS = 'APPROVED'—not in mapping; omit or add?
),
receipt_refunds AS (
    SELECT
        bu.bu_name AS business_unit, -- mapping: BU name from org_id; using fun_all_business_units_v (SCM refund report uses hr_organization_units—confirm standard for FIN integrations)
        rso.sales_order_number,
        cr.receipt_number AS transaction_number,
        rm.name AS transaction_type, -- mapping: receipt method from receipt_method_id on the refund receipt
        cr.receipt_date AS transaction_date,
        cr.amount AS transaction_amount, -- mapping: full receipt amount, not applied/unapplied portion—confirm for partial refunds
        cr.currency_code AS currency, -- mapping: currency column blank in spreadsheet—assumed currency_code
        app.amount_applied AS refund_amount,
        app.application_ref_num AS refund_number, -- mapping: "use receipt_id to derive"—implemented as application_ref_num only; confirm if lookup via cash_receipt_id is required instead
        app.apply_date AS refund_date,
        CASE
            WHEN cr.attribute_category = 'Non Insurance' THEN cr.attribute1 -- mapping: exact category + attribute1; validate literal spelling/casing in prod flexfields
        END AS sales_order_payment_id
    FROM ar_receivable_applications_all app
    JOIN unpaid_ap_refund ap
        ON ap.invoice_id = app.application_ref_id -- assumption: application_ref_id = AP payment request invoice_id for AP_REFUND_REQUEST—validate in UAT
    JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = app.cash_receipt_id
    JOIN ar_receipt_methods rm
        ON rm.receipt_method_id = cr.receipt_method_id
    JOIN allowed_receipt_methods arm
        ON arm.name = rm.name -- enforces mapping receipt-method allow list on the refunded receipt itself
    JOIN receipt_sales_orders rso
        ON rso.cash_receipt_id = cr.cash_receipt_id
    JOIN fun_all_business_units_v bu
        ON bu.bu_id = cr.org_id
    WHERE app.application_ref_type = 'AP_REFUND_REQUEST' -- mapping: application type Refund
      AND app.status = 'APP' -- not in mapping; excludes UNAPP reversal rows Oracle creates on unapply—confirm only APP rows are intended
      AND app.cash_receipt_id IS NOT NULL -- splits receipt vs CM paths; mapping does not define split—risk of duplicate/missed rows if both IDs populated
      AND (
            (
                :P_FROM_DATE IS NOT NULL
                AND :P_TO_DATE IS NOT NULL
                AND app.apply_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE) -- date params not in mapping; apply_date vs receipt_date vs AP invoice creation_date?
            )
            OR cr.receipt_number IN (:P_RECEIPT_NUMBERS) -- params not in mapping; empty BI Publisher bind list can error—confirm OIC always passes dates or values
            OR app.application_ref_num IN (:P_REFUND_NUMBERS)
        )
),
credit_memo_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        cm.ct_reference AS sales_order_number, -- mapping: CT_Reference; exchange-order note in col 5 applies to receipt method, not this field
        cm.trx_number AS transaction_number,
        orm.receipt_method_name AS transaction_type, -- mapping lists ar_cash_receipts_all/receipt_method_id for CM too—sourced via original SO receipt, not CM header
        cm.trx_date AS transaction_date,
        cma.transaction_amount,
        cm.invoice_currency_code AS currency, -- mapping: currency only on receipt row in spreadsheet—assumed invoice_currency_code for CM
        app.amount_applied AS refund_amount,
        app.application_ref_num AS refund_number, -- mapping: "use customer_trx_id to derive"—same open question as receipt path
        app.apply_date AS refund_date,
        NULL AS sales_order_payment_id -- mapping: field only on receipt path (attribute1)—intentionally null for CM
    FROM ar_receivable_applications_all app
    JOIN unpaid_ap_refund ap
        ON ap.invoice_id = app.application_ref_id
    JOIN ra_customer_trx_all cm
        ON cm.customer_trx_id = app.customer_trx_id
    JOIN cm_amounts cma
        ON cma.customer_trx_id = cm.customer_trx_id
       AND cma.org_id = cm.org_id
    JOIN order_receipt_method orm
        ON orm.sales_order_number = cm.ct_reference -- see order_receipt_method CTE: exchange orders may not match paid receipt on ct_reference
    JOIN fun_all_business_units_v bu
        ON bu.bu_id = cm.org_id
    WHERE app.application_ref_type = 'AP_REFUND_REQUEST'
      AND app.status = 'APP'
      AND app.customer_trx_id IS NOT NULL
      AND app.cash_receipt_id IS NULL -- excludes apps tied to both receipt and CM; confirm with functional team
      AND (
            (
                :P_FROM_DATE IS NOT NULL
                AND :P_TO_DATE IS NOT NULL
                AND app.apply_date BETWEEN CAST(:P_FROM_DATE AS DATE) AND CAST(:P_TO_DATE AS DATE)
            )
            OR cm.trx_number IN (:P_CREDIT_MEMO_NUMBERS)
            OR app.application_ref_num IN (:P_REFUND_NUMBERS)
        )
)
SELECT *
FROM receipt_refunds
UNION ALL
SELECT *
FROM credit_memo_refunds -- one row per receivable application; multiple APP rows per refund possible per Oracle AR behavior—confirm expected grain for OIC

```


## V2 - validated - not optimized
```sql
-- AP-I-3006: Initiate B2C Customer Refund in Payment Services
-- Extracts unpaid Receivables refund payment requests for Stripe / PayPal / Affirm receipt methods.
WITH allowed_receipt_methods AS (
    SELECT
        rm.receipt_method_id,
        rm.name
    FROM ar_receipt_methods rm
    WHERE rm.name IN (
        'CHASUS-0257-Stripe',
        'ROYCCA-2198-Stripe',
        'CHASUS-0257-PayPal',
        'CHASUS-0257-Affirm'
    )
),
unpaid_ap_refunds AS (
    SELECT
        api.invoice_id,
        api.invoice_num,
        api.org_id
    FROM ap_invoices_all api
    WHERE api.source = 'Receivables'
      AND api.payment_status_flag = 'N'
      AND api.invoice_type_lookup_code = 'PAYMENT REQUEST'
),
refund_applications AS (
    SELECT
        ra.receivable_application_id,
        ra.org_id,
        ra.cash_receipt_id,
        ra.customer_trx_id,
        ra.application_ref_num,
        ra.amount_applied,
        ra.apply_date
    FROM ar_receivable_applications_all ra
    INNER JOIN unpaid_ap_refunds api
        ON api.invoice_id = ra.application_ref_id
       AND api.org_id = ra.org_id
    WHERE ra.application_ref_type = 'AP_REFUND_REQUEST'
      AND ra.status = 'ACTIVITY'
      AND ra.applied_payment_schedule_id = -8
      AND ra.amount_applied > 0
),
receipt_sales_orders AS (
    SELECT
        remit.cash_receipt_id,
        MAX(remit.invoice_reference) AS sales_order_number
    FROM ar_cash_remit_refs_all remit
    GROUP BY remit.cash_receipt_id
),
cm_amounts AS (
    SELECT
        cm.customer_trx_id,
        cm.org_id,
        SUM(l.extended_amount) AS transaction_amount
    FROM ra_customer_trx_all cm
    INNER JOIN ra_customer_trx_lines_all l
        ON l.customer_trx_id = cm.customer_trx_id
       AND l.org_id = cm.org_id
    GROUP BY
        cm.customer_trx_id,
        cm.org_id
),
cm_invoice_links AS (
    SELECT DISTINCT
        cm.customer_trx_id,
        cm.org_id,
        inv.customer_trx_id AS invoice_trx_id
    FROM ra_customer_trx_all cm
    INNER JOIN ra_customer_trx_all inv
        ON inv.ct_reference = cm.ct_reference
       AND inv.org_id = cm.org_id
       AND inv.customer_trx_id <> cm.customer_trx_id
       AND inv.trx_class = 'INV'
    UNION
    SELECT DISTINCT
        cm.customer_trx_id,
        cm.org_id,
        app.applied_customer_trx_id AS invoice_trx_id
    FROM ra_customer_trx_all cm
    INNER JOIN ar_receivable_applications_all app
        ON app.customer_trx_id = cm.customer_trx_id
       AND app.applied_customer_trx_id IS NOT NULL
       AND app.application_type = 'CM'
       AND app.status = 'APP'
),
cm_original_receipts AS (
    SELECT
        cil.customer_trx_id,
        cil.org_id,
        MAX(rm.name) KEEP (
            DENSE_RANK FIRST ORDER BY cr.receipt_date DESC, rcpt_app.receivable_application_id DESC
        ) AS receipt_method_name
    FROM cm_invoice_links cil
    INNER JOIN ar_receivable_applications_all rcpt_app
        ON rcpt_app.applied_customer_trx_id = cil.invoice_trx_id
       AND rcpt_app.cash_receipt_id IS NOT NULL
       AND rcpt_app.status = 'APP'
    INNER JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = rcpt_app.cash_receipt_id
    INNER JOIN allowed_receipt_methods rm
        ON rm.receipt_method_id = cr.receipt_method_id
    WHERE NVL(cr.attribute_category, 'Non Insurance') = 'Non Insurance'
    GROUP BY
        cil.customer_trx_id,
        cil.org_id
),
receipt_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        rso.sales_order_number,
        cr.receipt_number AS transaction_number,
        rm.name AS transaction_type,
        cr.receipt_date AS transaction_date,
        cr.amount AS transaction_amount,
        cr.currency_code AS currency,
        ABS(ra.amount_applied) AS refund_amount,
        ra.application_ref_num AS refund_number,
        ra.apply_date AS refund_date,
        CASE
            WHEN cr.attribute_category = 'Non Insurance' THEN cr.attribute1
        END AS sales_order_payment_id
    FROM refund_applications ra
    INNER JOIN ar_cash_receipts_all cr
        ON cr.cash_receipt_id = ra.cash_receipt_id
    INNER JOIN allowed_receipt_methods rm
        ON rm.receipt_method_id = cr.receipt_method_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cr.org_id
    LEFT JOIN receipt_sales_orders rso
        ON rso.cash_receipt_id = cr.cash_receipt_id
    WHERE ra.cash_receipt_id IS NOT NULL
),
credit_memo_refunds AS (
    SELECT
        bu.bu_name AS business_unit,
        cm.ct_reference AS sales_order_number,
        cm.trx_number AS transaction_number,
        cor.receipt_method_name AS transaction_type,
        cm.trx_date AS transaction_date,
        ABS(ca.transaction_amount) AS transaction_amount,
        cm.invoice_currency_code AS currency,
        ABS(ra.amount_applied) AS refund_amount,
        ra.application_ref_num AS refund_number,
        ra.apply_date AS refund_date,
        CAST(NULL AS VARCHAR2(150)) AS sales_order_payment_id
    FROM refund_applications ra
    INNER JOIN ra_customer_trx_all cm
        ON cm.customer_trx_id = ra.customer_trx_id
       AND cm.org_id = ra.org_id
    INNER JOIN cm_amounts ca
        ON ca.customer_trx_id = cm.customer_trx_id
       AND ca.org_id = cm.org_id
    INNER JOIN fun_all_business_units_v bu
        ON bu.bu_id = cm.org_id
    INNER JOIN cm_original_receipts cor
        ON cor.customer_trx_id = cm.customer_trx_id
       AND cor.org_id = cm.org_id
    WHERE ra.cash_receipt_id IS NULL
      AND ra.customer_trx_id IS NOT NULL
)
SELECT *
FROM receipt_refunds
WHERE (
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND refund_date >= CAST(:P_FROM_DATE AS DATE)
        AND refund_date <= CAST(:P_TO_DATE AS DATE)
    )
    OR :P_TRANSACTION_NUMBER IN (transaction_number, refund_number)
)
UNION ALL
SELECT *
FROM credit_memo_refunds
WHERE (
    (
        :P_FROM_DATE IS NOT NULL
        AND :P_TO_DATE IS NOT NULL
        AND refund_date >= CAST(:P_FROM_DATE AS DATE)
        AND refund_date <= CAST(:P_TO_DATE AS DATE)
    )
    OR :P_TRANSACTION_NUMBER IN (transaction_number, refund_number)
)
```

## V1 - optimized - not validated - with assumptions like joins

```sql
WITH eligible_receipt_methods AS (
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
-- AP-I-3006: unpaid AR refund requests eligible for Payment Services (mapping: AP_REFUND_REQUEST, not paid in AP, source Receivables).
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
    -- Mapping requires not paid in AP; AP-side filters mirror AP-I-3004 (WP_AP_INVOICE_HOLDS_DM) payment request / Receivables / unpaid.
    INNER JOIN ap_invoices_all api
        -- TODO: validate join key in evdi-test; mapping does not specify link—application_ref_num = invoice_num (+ org_id) is a reasonable guess (alt: application_ref_id = invoice_id).
        ON api.invoice_num = ra.application_ref_num
        AND api.org_id = ra.org_id
    WHERE ra.application_ref_type = 'AP_REFUND_REQUEST' -- mapping: Application_ref_type = 'AP_REFUND_REQUEST'
        -- TODO: not in AP-I-3006 mapping; common AR convention only—confirm or remove (AP-I-3004 uses api.approval_status = 'APPROVED' on AP side instead).
        -- AND ra.status = 'APP'
        -- AND api.invoice_type_lookup_code = 'PAYMENT REQUEST'
        AND api.source = 'Receivables'
        AND api.payment_status_flag = 'N' -- mapping: not paid in Accounts Payable
        -- Report parameters applied here to limit rows before receipt/credit-memo branches (not in mapping).
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