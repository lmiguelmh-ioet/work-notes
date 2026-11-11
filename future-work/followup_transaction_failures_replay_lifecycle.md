# Ticket draft — transaction_failures: incident identity model + replay lifecycle

DRAFT ONLY — for review; to be filed by the team. Parked from OTCM-138123 scope on
2026-11-11; deferred to future-work the same day (lead decision, Gabriel: table work
out of scope). OTCM-138123's PR4a (replay context + SO publish gate + publish
ledger) folds in here — without the ledger it was inert scaffolding in that ticket.
The ledger's design grew into the one-table state store: see
`one_table_state_store_baseline.md` beside this file.

## Summary

Redesign the `transaction_failures` identity model so a failure *incident* is distinguishable
from a failure *signature*, then build the replay lifecycle (claim, outcome, expiry) on top of it.

## Problem

The table holds one row per (rice_id, order_id, error signature). That 1:1 identity conflates
the signature with every incident that ever matched it:

- A RESOLVED row reopens on any same-signature recurrence, even months later — a new incident
  flips a closed one. Without TTL on the deployed tables there is no expiry bound at all.
- A FAILED row accumulates unrelated recurrences: occurrence_count and invocations blend
  incidents months apart; first_failed_at reads like a continuous outage.
- The row's payload pointer is ambiguous for replay: first failure's transaction id vs. the
  latest recurrence's payload fields. A reprocess cannot tell which incident it re-runs.
- Claim semantics are ill-defined: claiming the row claims every past and future incident of
  the signature.

Surfaced while designing safe reprocess of WMS-I-1005 pick confirmations (OTCM-138123); the
replay lifecycle was parked out of that ticket's scope for this reason.

## Proposal (directions to decide, not prescriptive)

1. Incident-level rows: key carries an occurrence/incident component (e.g. first failure id
   or ULID), signature row becomes an aggregate or disappears.
2. Incident substructure: one signature row with a bounded list of incident entries, each
   with its own status and payload pointer.
3. Signature row + separate incidents table (read model stays on signatures, lifecycle acts
   on incidents).

Then design the lifecycle on the chosen model: atomic claim (RETRYING with lease), outcome
write-back (RESOLVED/FAILED/DEAD), TTL on RESOLVED, no resurrection of IGNORED/DEAD, and an
unambiguous payload per replay.

## Reference material

- Parked branch `OTCM-138123-transaction-failure-replay-lifecycle` (uncommitted working tree
  in Luis's checkout) holds a reference implementation of the lifecycle pieces: writer reopen
  semantics with evidence-only fallback, TransactionFailureStatusUpdateAction port + DynamoDB
  adapter (claim with 1h lease, outcome stamping, ttl), record/mapper fields, LocalStack TTL
  block. Salvage what fits once the identity model is decided.
- TTL is already enabled on every deployed table (infra-terraform,
  service-monocle-integration/dynamodb, ttl attribute) — no SRE ask needed; the lifecycle
  only writes the attribute on RESOLVED rows. The tables also have DynamoDB streams enabled
  (NEW_AND_OLD_IMAGES).

## Acceptance criteria (draft)

- Identity model decided and documented; coexistence/migration plan for existing rows.
- A replay targets one unambiguous incident payload.
- Claim and outcome transitions are atomic; a crashed reprocess is reclaimable after a lease.
- Live-path recurrence never resurrects IGNORED/DEAD and never corrupts an in-flight claim.

## Relations

- Parked out of OTCM-138123 (WMS-I-1005 idempotency) — that ticket ships the idempotency
  changes that make any future replay safe; this ticket is the replay mechanism itself.
- Related: OTCM-139192 (transaction_failures read API) — the future reprocess route would
  extend that surface.
