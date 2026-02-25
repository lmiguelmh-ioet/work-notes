### Stripe

| Resource                          | URL                                                   |
| --------------------------------- | ----------------------------------------------------- |
| Payout Reconciliation (Dashboard) | https://dashboard.stripe.com/reports/reconciliation   |
| Reports / export options          | https://dashboard.stripe.com/reports                  |
| Payout reconciliation docs        | https://docs.stripe.com/reports/payout-reconciliation |
| Reports API (programmatic)        | https://docs.stripe.com/reports/api                   |

How to download:
1. Log in at https://dashboard.stripe.com
2. Go to Reports → Reconciliation (or Payments → Payouts)
3. Choose date range
4. Click Download and choose the itemized CSV (use reporting_category = charge, refund, partial_capture_reversal)
### PayPal

| Resource                     | URL                                                                         |
| ---------------------------- | --------------------------------------------------------------------------- |
| Reports portal (after login) | https://www.paypal.com/myaccount/transactions/                              |
| Activity Download docs       | https://developer.paypal.com/docs/reports/online-reports/activity-download/ |
| T-code reference             | https://developer.paypal.com/docs/reports/reference/tcodes/                 |

How to download:
1. Log in at https://www.paypal.com
2. Go to Reports (or Activity → Reports)
3. Use Activity Download
4. Pick date range and CSV
5. In “Customize report fields”, include at least: Date, Gross, Transaction ID, Transaction Event Code, Reference Txn ID

### Affirm

| Resource                      | URL                                                                                               |
| ----------------------------- | ------------------------------------------------------------------------------------------------- |
| Merchant Portal (Settlements) | https://www.affirm.com/dashboard/signin (then Settlements)                                        |
| Settlement reports (access)   | https://businesshub.affirm.com/hc/en-us/articles/11218194202260-Accessing-your-settlement-reports |
| Sample settlement report      | https://businesshub.affirm.com/hc/en-us/article_attachments/32119988169620                        |

Note: Some Affirm Business Hub pages require login and may be gated.

How to download:
1. Log in at https://www.affirm.com/dashboard/signin
2. Go to Settlements
3. Download the desired report for the date range
4. For SFTP or email delivery, contact Merchant Care: merchanthelp@affirm.com
