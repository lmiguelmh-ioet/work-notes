# OTCM-138123 — Jira drafts (user posts; agent never creates/transitions)

## 1. Comment on OTCM-138123 — amendment to comment 983437

Amendment to comment 983437 (the post-ship status contract): the split it recorded — Shipped and Shipped and interfaced fail with a ticket while Interfaced and Pending inventory processing skip — is superseded. Review feedback showed the four statuses are only seconds of Oracle interface progress apart (prod lines interface 7–28s after ship confirm), so a status-name split made the same redelivery ticket or skip depending on timing.

Per FSD §10 row 3, all four post-ship statuses now share one rule on the pick-confirmation path: a request-matched line with picked quantity > 0 is a duplicate and skips with no ERP writes and no ticket; picked quantity == 0 fails the order with the "ship confirmed and not yet picked" ticket. Staged stays an unconditional skip. An explicit PickedQuantity null from Oracle reads as 0. Implemented in PR #2900, commit 2e16822b2.

## 2. R4.16 — functional boundary question (picked > 0 but partial)

**Question:** On the quantity gate, a post-ship line with 0 < picked < ordered (a partial pick that still reached ship confirm) currently skips as a duplicate on redelivery, same as a fully picked line — any pick evidence counts. Is that the intended reading of FSD §10 row 3, or should a partial quantity fail for review instead?

**Context:** Prod payload backups carry no negative picked quantities (all-time error payloads plus the full final archive day — 15,963 files). Most lines are unit picks, but multi-quantity picks up to 600 occur. The WMS payload carries no ordered quantity, so a partial-pick line cannot be spotted from these files alone. The answer should be on record before the first partial-pick redelivery arrives.

**Where to ask:** WMS-I-1005 FSD §10 comment thread (the row-3 discussion Guillermo opened) — reply in that thread; and attach the answer to the follow-up ticket below once filed.

## 3. Follow-up ticket draft — for the user to file (never agent-created)

**Project:** OTCM · **Type:** Task · **Summary:** [WMS-I-1005] Confirm partial-pick boundary on the pick-confirmation quantity gate

**Description:**

PR #2900 (OTCM-138123) gates all four post-ship statuses on picked quantity for WMS-I-1005 redeliveries: picked quantity > 0 skips as a duplicate; == 0 fails with the "ship confirmed and not yet picked" ticket. A line with 0 < picked < ordered quantity currently skips exactly like a fully picked line.

Prod payload backups carry no negative picked quantities (all-time error payloads plus the full final archive day); most lines are unit picks, with multi-quantity picks up to 600. Functional to confirm the intended reading of FSD §10 row 3:

- Any pick evidence means the confirmation was already processed → keep the current `> 0` gate.
- A partial quantity needs review → fail with a ticket instead of skipping.

If the answer changes the rule, update the classifier gate in `_shipment_line_classifier.py` and the FSD §10 row 3 wording in the same change.

**Acceptance criteria:**

- Functional answer recorded on this ticket (or linked FSD thread).
- If the rule changes: classifier gate + tests updated, FSD §10 row 3 reworded.
