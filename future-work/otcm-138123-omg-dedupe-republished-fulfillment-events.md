# Jira ticket DRAFT — never filed by the agent; for Luis to file (or route)

Source: PR #2900 review triage, finding 20261112T0924_3. Owner accepted the risk
(2026-11-12). Consequence class disputed financial/data vs operational; the
conservative reading (financial/data) requires this durable record.

---

## Summary

[OTCM-XXXXX] Confirm OMG dedupe for republished WMS-I-1005 fulfillment events

## Description

WMS-I-1005 (OTCM-138123) skips the Oracle leg when the request-matched shipment
lines need no pick work (statuses Not shipped / Not applicable) and publishes the
OMG fulfillment event anyway. A redelivery of the same pick confirmation takes the
same path, so the event publishes a second time for the same order.

Whether OMG dedupes that event (for example by transaction_id) is unconfirmed. If
it does not, a redelivery could double-count the order downstream.

This exposure predates OTCM-138123: on main, every no-work order already republished
on redelivery. The PR does not widen it; it makes the path explicit and named.

## Scope

1. Confirm with the OMG team whether the fulfillment-event consumer dedupes by
   transaction_id or any idempotency key.
2. If it does: record the evidence here and close.
3. If it does not: pick the fix — withhold the publish on redelivery (needs the
   replay ledger parked in OTCM-138123) or an OMG-side dedupe — and file the
   follow-up.

## Acceptance criteria

- [ ] Written answer from the OMG side on transaction_id dedupe for fulfillment
      events, linked here.
- [ ] If there is no dedupe: a linked follow-up ticket with the chosen fix.
