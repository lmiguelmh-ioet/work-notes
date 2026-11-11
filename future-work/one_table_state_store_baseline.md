# One-table state store — baseline proposal

> PARKED 2026-11-11 — lead decision (Gabriel): the state-table work is out of
> scope and unscheduled. Unfiled draft; re-verify claims against the repo when
> picked up (grown out of OTCM-138123 PR4a's publish ledger).

Monocle's general-purpose state store. Follows the OMG `order_domain` single-table
precedent: generic keys, entity prefixes, sparse GSIs, per-item TTL.

v1.1 — validated against the live repo by an independent design panel (3 designers)
and hardened by adversarial review (2 reviewers). All write paths are single-item
conditional writes; no read-then-write anywhere.

## Scope: two tickets

**Ticket A — table + `EFFECT#` ledger.** Create the table and ship the
side-effect ledger family with its first adopter (WMS-I-1005 publish ledger,
OTCM-138123 PR4a). No GSIs, no stream consumers, no payloads — the EFFECT
access patterns are key-based only (`BatchGetItem` + `PutItem`). The
`CHECKPOINT#` family's key convention is fixed here too; its first
implementation waits for a concrete adopter.

**Ticket B — `FAILURE#` migration (later).** Move the incident registry off
`transaction_failures`: the FAILURE item family, the three read GSIs, the
replay write paths (claim/stamp), the OEH stream consumer + TTL sweeper, the
S3 payload lifecycle, and the cutover plan. Everything failure-shaped below
is marked **(Ticket B)**; it is designed now so Ticket A's table choices
(key schema, stream, TTL) already fit it.

One-way-door note: only the table name, key schema (`PK`/`SK`), and encryption
are frozen at creation — TTL, streams, and GSIs are all addable online later,
so the split costs nothing.

## Table fundamentals

| Property | Proposal |
|---|---|
| Name | `wp-monocle-integrations-<env>-state` |
| Keys | `PK` (S), `SK` (S) |
| Billing | On-demand (traffic is low and spiky) |
| TTL | Attribute `ttl` (N, epoch seconds), per-item opt-in; enabled at creation, first expiring rows arrive with Ticket B |
| Stream | NEW_AND_OLD_IMAGES from day one, no consumers until Ticket B (OEH automation + TTL sweeper — see Streams) |
| PITR + deletion protection | Enabled (prod incident data + integration state) |
| Encryption | Same as current module (AWS-owned key) |

## Key conventions

- `PK` carries the entity prefix: `FAILURE#<failure_id>`,
  `EFFECT#<integration>#<step>#<dedupe-key>`, …
- `SK` is a singleton: `META`. One item per entity; there are no child items.
  `META` is a constant placeholder — DynamoDB requires the sort key on every
  item — kept because a sort key cannot be added to a table later: it leaves
  the door open for a future family with real item collections (several SKs
  under one PK, loaded together with one `Query`).
- Timestamps: ISO-8601 UTC for business fields (`last_failed_at`, …); epoch
  **Number** for `ttl` and `claim_expires_at` (machine comparisons stay
  type-safe across Lambdas).
- Payloads live in S3 (versioned bucket); the item carries
  `payload_bucket` / `payload_key` / `payload_version_id` pointers. Nothing
  inline — payload size is unbounded and the detail route's contract returns
  pointers today. (Ticket B — only FAILURE rows carry payloads.)

### Key anatomy

```text
FAILURE # WMS-I-1005 # SO-1001 # 9f2c4a1b7e03    per-order incident
FAILURE # WMS-I-1005 # e4d2a90c1f55              global (run-scoped) incident
EFFECT  # WMS-I-1005 # publish_fulfillment_pick_event # <sha256…>
   │          │                     │
   │          │                     └─ family-defined tail
   │          └─ integration
   └─ entity family
```

The family token is the only universal segment — each family defines its own
trailing shape. All family values:

| Family | Purpose | Example key | Status |
|---|---|---|---|
| `FAILURE` | Incident registry (replaces transaction_failures) | `FAILURE#WMS-I-1005#SO-1001#9f2c4a1b7e03` | Ticket B |
| `EFFECT` | Side-effect ledger ("did this effect complete?") | `EFFECT#WMS-I-1005#publish_fulfillment_pick_event#<sha256>` | Ticket A — first tenant (WMS-I-1005 PR4a) |
| `CHECKPOINT` | Per-integration in-flight state machines (e.g. ESS job submitted, outcome unknown) | `CHECKPOINT#WMS-I-1005#ess_submission#<id>` | Ticket A fixes the key convention; first implementation needs a concrete adopter |
| _next state need_ | A new family value, never a new table | — | — |

### FAILURE identity — legacy `failure_id` preserved verbatim

The string after `FAILURE#` **is** today's `failure_id`
(`TransactionFailure.failure_id`), so every stored reference (Jira tickets,
runbooks, bookmarks) resolves unchanged after migration:

- **Per-order**: `<rice>#<order_id>#<sig12>` — e.g. `WMS-I-1005#SO-1001#9f2c4a1b7e03`.
- **Global** (no order id): `<rice>#<sig12>` — e.g. `WMS-I-1005#e4d2a90c1f55`.

`sig12 = sha256(error_signature)[:12]`, exactly as the current domain computes
it. The two shapes are unambiguous by segment count (3 vs 2), so no kind segment
is inserted — inserting one (e.g. `ORD#`) would orphan every stored legacy id.

Why signature-based identity (and not source-event identity):

- **Same defect → same row.** A recurring failure lands on the same key, so
  reopen is a conditional update, never a second row. Per-run uuid keys cannot
  do that.
- **Storm aggregation.** An upstream outage failing N events with the same
  defect reopens ONE row and bumps `occurrence_count` — one ops-queue entry,
  one OEH ticket — instead of N rows and N tickets while the system is degraded.
- **Defect separation.** Two different defects on the same order or event are
  two rows, because the signature differs.
- **Replayability is preserved** without per-event rows: replay always
  reprocesses the row's *latest* payload pointer (evidence is refreshed on
  every occurrence — today's behavior).

## Item families (first two tenants)

### `FAILURE#<failure_id>`, `SK=META` — incident registry **(Ticket B)**

One item carries everything:

| Field group | Fields |
|---|---|
| Identity | `PK`, `SK`, `failure_id` (string after `FAILURE#`), `rice_id`, `order_id` (sparse), `error_signature` |
| State | `status` (`FAILED`/`RETRYING`/`RESOLVED`/`DEAD`/`IGNORED`), `error_code`, `failed_step` |
| Evidence | `occurrence_count`, `first_failed_at`, `last_failed_at`, `invocations` (append-only list of recent occurrences), `payload_request` / `payload_response` (S3 pointers; response sparse) |
| Replay lifecycle | `retry_count`, `last_retry_at`, `retry_claim` (ULID fencing token), `claim_expires_at` (N epoch), `reprocessed_at`, `reprocessed_by` |
| Expiry | `ttl` (N epoch; only on RESOLVED) |
| Index | none — the GSIs key on `status`, `rice_id`, `order_id`, `last_failed_at` directly (sparse) |

Notes:

- `payload_request` is **the replayable unit, not a wire transcript**: the
  input the replay path re-executes, per the integration's registered
  deserializer (for WMS-I-1005 it is the source pick payload; an
  API-call-shaped failure may store the exact request body). Sibling rows of
  one run point at the same S3 object — each row carries its own pointer
  because rows are independent (there is no parent lookup). A row with no
  meaningful replayable unit carries no pointer; the reprocess route refuses
  it with a distinct "no replayable payload" (≠ "payload missing": pointer
  set, object gone).
- `IGNORED` is today's muted-terminal status: recurrences refresh evidence only;
  it never re-enters the ops queue (see Write paths).
- `invocations` is **uncapped** — entries are tiny and 400 KB is unreachable at
  realistic occurrence counts (today's writer also appends uncapped). If a
  chronic row ever threatens the item limit, invocation history moves to the S3
  payload object; the cap is not implementable as a single conditional write.
- `retry_count` is per-episode: the reopen upsert resets it to 0, so the retry
  budget applies per incident episode, not across the row's lifetime.

### `EFFECT#<integration>#<step>#<dedupe-key>`, `SK=META` — side-effect ledger **(Ticket A)**

Records that an externally visible effect completed: published a message,
called an API, submitted an ESS job. Existence = done; there is no "started"
state (in-flight state machines belong to `CHECKPOINT#`, a later family).

| Field | Contents |
|---|---|
| `completed_at` | When the effect landed |
| `tracking_id` | Run/attempt id |
| `reference` | The external handle: SQS/SNS MessageId, ESS request id, API response id — makes "did it go out?" support lookups traceable |
| `ttl` | **Never** — see TTL policy |

Hard rule for adopters: the dedupe key is the same deterministic formula the
effect's own transport uses as its FIFO `message_deduplication_id`, never a
run-scoped id. Verified formulas:

- WMS-I-1005 SO publish (SQS FIFO): `sha256(org-ship_set-fr_ids-event_timestamp)`
  — computed in `_so_pick_confirm_processor.py` and already used as the
  `message_deduplication_id`. Same payload → same sha, on every run and replay.
- WMS-I-1027R relay (SNS FIFO): `sha256(file_name)`.

First instance (PR4a): `EFFECT#WMS-I-1005#publish_fulfillment_pick_event#<sha256>`.
Ports are generic (`EffectLedgerReader` batch-get, `EffectLedgerStore`
conditional put); each integration derives its own keys.

### Future tenants (no schema change needed)

New state needs become new family values — `CHECKPOINT#` is the reserved next
one. Each is a new prefix, not a new table.

## GSIs (sparse — items without GSI keys don't appear) **(Ticket B)**

Ticket A creates no GSIs: the EFFECT patterns are key-based. Ticket B adds the
three indexes the read API (OTCM-139192) drives today, reusing the legacy
table's exact key shape — raw attributes, no duplicated `GSI*PK`/`GSI*SK`
fields, so the index tracks the attribute with no sync invariant to maintain:

| Index | Keys | Serves |
|---|---|---|
| status-lastFailedAt | `status` (hash), `last_failed_at` (range) | List per status (the ops-queue default) |
| riceId-lastFailedAt | `rice_id` (hash), `last_failed_at` (range) | List per integration |
| orderId-lastFailedAt | `order_id` (hash), `last_failed_at` (range) | List per order |

Generic `GSI*PK`-style overloading was considered and rejected: the indexes
stay failure-only by construction, so duplicated index attributes would buy
nothing. A future family that needs an index gets its own, added online.

Query semantics carry over unchanged: most specific filter picks the index
(order_id → rice_id → status), losing filters become `FilterExpression`, date
range is a sort-key condition on `last_failed_at`, sort flips
`ScanIndexForward`, cursor = encoded `LastEvaluatedKey` (tie-safe: the LEK
carries the full table + GSI keys, so bare-timestamp sort keys paginate
correctly). A reopened failure's `last_failed_at` update moves it within the
GSIs automatically.

Hot-partition note: every open incident sits in the single `status = FAILED`
index partition. At registry volumes (failures are error-rate, not event-rate)
this is far below the on-demand per-partition write ceiling. If a storm ever
threatens it, the escape hatch is a bucket suffix on the indexed value —
deferred with that trigger, since GSIs cannot be re-keyed online.

Future lookups (support by `reference`, sibling correlation) get GSI4+ when a
consumer needs them — adding a GSI to a live table is an online operation.

## Access patterns

Ticket A (EFFECT ledger — key-based only):

| Pattern | Served by |
|---|---|
| Batch-check effects before re-doing them | `BatchGetItem` with `ConsistentRead=true` on `EFFECT#` keys |
| Record an effect (first writer wins) | `PutItem`, `attribute_not_exists(PK)` |
| Support lookup ("did this go out?") | `GetItem` on the `EFFECT#` key → `completed_at` + `reference` |

Ticket B (FAILURE registry):

| Pattern | Served by |
|---|---|
| Get one failure | `GetItem(PK=FAILURE#<failure_id>, SK=META)` |
| List failures by status / rice_id / order_id, date-ranged, sorted, paged | the three GSIs |
| Record / reopen a failure | Conditional `UpdateItem` (+ conditioned evidence-only fallback) |
| Replay claim (FAILED→RETRYING with lease + fence) | Conditional `UpdateItem` |
| Outcome stamp (RESOLVED / FAILED / DEAD) | Conditional `UpdateItem` fenced by `retry_claim` |

## EFFECT write/read paths (Ticket A)

Record: `PutItem` with `attribute_not_exists(PK)` **after** the effect lands —
first writer wins; a condition failure is a no-op. Check: one `BatchGetItem`
with `ConsistentRead=true` over the candidate keys before acting — eventually
consistent reads can report a just-recorded effect as absent, widening the
check-then-act window for the common retry-immediately case; 2× read cost is
negligible at ledger volumes. The full check/record flow and its honesty
limits are scenario 5 below.

## FAILURE write paths (Ticket B — writers: failure recorder, replay lifecycle)

DynamoDB condition semantics that these paths rely on: a comparison against a
missing attribute evaluates UNKNOWN → the clause is FALSE. Every condition
below that tolerates a missing attribute says so explicitly.

### Record / reopen upsert

```text
SET     status = :failed,
        error_code = :code, failed_step = :step, error_signature = :sig,
        last_failed_at = :now,
        first_failed_at = if_not_exists(first_failed_at, :now),
        occurrence_count = if_not_exists(occurrence_count, :zero) + :one,
        invocations = list_append(if_not_exists(invocations, :empty), :new),
        retry_count = :zero,                  -- per-episode budget reset
        payload_request = :latest_pointer     -- (+ payload_response when present)
REMOVE  ttl, retry_claim, claim_expires_at, reprocessed_at, reprocessed_by
CONDITION attribute_not_exists(PK)
       OR (#status <> :retrying AND #status <> :ignored AND #status <> :dead)
```

- First occurrence and recurrences on FAILED/RESOLVED rows take this path.
  On a RESOLVED row it re-arms the incident (back to the ops queue, TTL
  removed); on a FAILED row it refreshes evidence in place.
- **IGNORED stays muted**: a recurrence fails the condition → evidence-only
  fallback. Today's `if_not_exists(status, FAILED)` behavior (status never
  flips a muted row) is preserved.
- **DEAD stays dead**: a recurrence is evidence-only too. The only exit from
  DEAD is an explicit admin action (ops triage), never an automatic reopen.

### Evidence-only fallback (on ConditionalCheckFailed)

```text
SET     last_failed_at = :now,
        occurrence_count = occurrence_count + :one,
        invocations = list_append(invocations, :new),
        payload_request = :latest_pointer
CONDITION #status IN (:retrying, :ignored, :dead)
```

The fallback is **conditioned**: without it, a recurrence racing a replay's
RESOLVED stamp would be silently swallowed (evidence lands on a resolved row,
no stream transition fires, the incident is lost). On a second
ConditionalCheckFailed (the race happened), loop back to the primary upsert —
bounded retries (suggest 3), then raise.

### Replay claim

```text
SET     status = :retrying,
        retry_claim = :claim_ulid,
        claim_expires_at = :now_plus_1h_epoch,
        retry_count = if_not_exists(retry_count, :zero) + :one,
        last_retry_at = :now
CONDITION (#status = :failed
       OR (#status = :retrying
           AND (attribute_not_exists(#claim_expires_at) OR #claim_expires_at < :now_epoch)))
      AND (attribute_not_exists(#retry_count) OR #retry_count < :budget)
```

- One claimant wins; concurrent claims get ConditionalCheckFailed → 409.
- Lease: 1 hour. A crashed replay's row is stealable once the lease expires.
  The `attribute_not_exists` disjunct matters for backfilled legacy rows, which
  carry no claim attributes — without it they could never be claimed (missing
  attribute → UNKNOWN → FALSE).
- Budget: suggest 5 attempts per episode. `attribute_not_exists(#retry_count)`
  tolerates pre-lifecycle rows.

### Outcome stamp (fenced)

Success:

```text
SET     status = :resolved,
        reprocessed_at = :now, reprocessed_by = :actor,
        ttl = :now_plus_90d_epoch
REMOVE  retry_claim, claim_expires_at
CONDITION #status = :retrying AND #retry_claim = :claim_ulid
```

Failure — two chained conditional writes, no read:

1. DEAD stamp: `SET status = :dead, <new error fields>`
   `REMOVE retry_claim, claim_expires_at`
   `CONDITION #status = :retrying AND #retry_claim = :claim_ulid AND #retry_count >= :budget`
2. On ConditionalCheckFailed, FAILED stamp: same minus the budget clause and
   plus `#retry_count < :budget`. On a second ConditionalCheckFailed the fence
   was lost (a newer claim owns the row) — the replay aborts; its result is
   discarded, never stamped.

The `retry_claim` ULID is the fencing token: a zombie replay whose lease was
stolen cannot stamp over the new owner's row.

### Status transitions

| From | To | Trigger | Side effects |
|---|---|---|---|
| — | FAILED | First occurrence (insert) | Evidence set, GSI keys set |
| FAILED / RESOLVED | FAILED | Record/reopen upsert | Evidence refreshed, `retry_count=0`, `REMOVE ttl` + claim attrs |
| IGNORED / DEAD | _(unchanged)_ | Recurrence → evidence-only fallback | Evidence refreshed, status untouched |
| FAILED / stale RETRYING | RETRYING | Replay claim | `retry_count+1`, lease + fence stamped |
| RETRYING | RESOLVED | Fenced success stamp | `reprocessed_at/by`, `ttl = now+90d`, claim attrs removed |
| RETRYING | FAILED | Fenced failure stamp (budget remains) | New error recorded, claim attrs removed |
| RETRYING | DEAD | Fenced failure stamp (budget exhausted) | Awaits ops triage; claim attrs removed |
| DEAD | FAILED | **Admin action only** | Explicit ops decision; never automatic |

Every transition is a single conditional write; the ops-queue index follows
`status` automatically, so the queue and the detail view never disagree.
`last_failed_at` is untouched by status flips: a RESOLVED row stays ordered by
when it last failed.

## How replay works (payload → re-execution) **(Ticket B)**

1. **Trigger**: reprocess route (follow-up ticket) with the failure's
   `failure_id`; manual Lambda invoke until then.
2. **Claim**: the conditional claim above flips FAILED→RETRYING (or steals an
   expired lease), stamps fence + budget. Only one concurrent replay wins.
3. **Load**: `GetItem` on the row; the request body is fetched from S3 via the
   item's pointer. A missing payload (past the retention horizon) is a
   distinct refusal — "payload missing", not "row missing".
4. **Rebuild**: the integration's registered deserializer turns the payload
   back into its request model; `reprocessed_by` records the actor.
5. **Re-execute** with a replay context. Two skip layers:
   - **Coarse** — the row's `failed_step` skips steps known-good (e.g.
     suppress the DST upload).
   - **Fine** — every side-effecting step checks `EFFECT#` first: present →
     skip; absent → execute and record. Covers partial progress `failed_step`
     cannot see (half a batch sent before the exception).
6. **Outcome**: the fenced stamps above (RESOLVED, or FAILED/DEAD by budget).

## Stream consumers **(Ticket B)**

The stream fires for every entity family. Two consumers, both driven off the
stream:

1. **OEH error-ticket automation.** Today tickets are created **inline** in
   the event handlers' exception paths; the stream consumer replaces that
   (cutover in Migration). ESM filter pattern:

   ```text
   PK begins_with "FAILURE#"  AND  NewImage.status IN ["FAILED", "DEAD"]
   ```

   Consumer transition guard (old image vs new image):

   | old.status | new.status | Action |
   |---|---|---|
   | absent (INSERT) | FAILED | Open ticket — new incident |
   | RESOLVED | FAILED | Open ticket — reopened incident |
   | DEAD | FAILED | Open ticket — admin-reopened |
   | FAILED | FAILED | None — recurrence evidence |
   | RETRYING | FAILED | None — a failed replay attempt on an already-ticketed incident |
   | any | DEAD | Escalate — retry budget exhausted; a human is needed |
   | any | RETRYING / RESOLVED | None |

   This changes ticket-noise semantics on purpose: today every occurrence
   tickets; post-cutover only transitions ticket. Called out as an intentional
   behavior change in the rollout notes.

   Filter/amplification note: ESM filters evaluate the NewImage only, so every
   FAILED→FAILED recurrence MODIFY still invokes the consumer Lambda, which
   the guard then drops. Accepted at registry volumes; the consumer gets
   reserved concurrency so a failure storm cannot starve it.

2. **TTL payload sweeper.** TTL deletes appear on the stream as REMOVE events
   whose `userIdentity` is the DynamoDB service principal. The sweeper
   deletes the expired row's S3 payload objects (all versions) — the row's
   TTL is the payload's deletion signal (see Payload lifecycle).

## TTL policy **(Ticket B for FAILURE rows)**

| Row state | `ttl` |
|---|---|
| FAILED / RETRYING / IGNORED | None — open incidents never expire |
| RESOLVED | `resolved_at + 90d` |
| DEAD | None — the audit tail that invites later replay or triage |
| EFFECT | **None, ever** — the ledger must outlive any row it protects: a replay of a long-dead incident after ledger expiry would find "no record" and re-execute the side effect. Rows are KBs and cheap. (Alternative considered and rejected: 90d expiry + a hard replay cut-off.) |

## Payload lifecycle **(Ticket B)**

The registry's payloads are order/customer data; their lifetime must be
bounded deliberately, in both directions:

- **Row expires → payload dies.** The TTL sweeper (above) deletes payloads of
  TTL-expired rows. A DynamoDB TTL delete is the only row-deletion path, so
  the sweeper covers all expiry.
- **Safety net.** An S3 lifecycle rule on the payload prefix expires current +
  noncurrent versions past a generous horizon (suggest 400d) — catches orphans
  (sweeper misses, manual row deletes).
- **Reverse skew.** A payload must never die while its row lives: DEAD rows
  persist and so do their payloads (the 400d net only reaps objects whose
  rows are gone). If a replay ever finds the pointer dangling (payload reaped
  by the net after manual row deletion), the replay refuses with a distinct
  "payload missing" error.

## Scenario walkthroughs

### 1. A run records failures: two per-order rows + one global

A WMS-I-1005 pick payload arrives. Orders `SO-1001` and `SO-1002` fail ERP
confirmation with the same defect (error signature sha `9f2c4a1b7e03`); the
run then aborts before publishing — a global failure whose defect hashes to
`e4d2a90c1f55`.

Three items are written (one per incident; payloads go to S3):

```json
[
  {
    "PK": "FAILURE#WMS-I-1005#e4d2a90c1f55",
    "SK": "META",
    "status": "FAILED",
    "failed_step": "publish_fulfillment_pick_event",
    "rice_id": "WMS-I-1005",
    "occurrence_count": 1,
    "first_failed_at": "2026-11-11T14:02:11Z",
    "last_failed_at": "2026-11-11T14:02:11Z",
    "retry_count": 0,
    "payload_request": {"bucket": "…", "key": "…/pick_payload.json", "version_id": "…"}
  },
  {
    "PK": "FAILURE#WMS-I-1005#SO-1001#9f2c4a1b7e03",
    "SK": "META",
    "status": "FAILED",
    "failed_step": "erp_pick_confirm",
    "order_id": "SO-1001",
    "rice_id": "WMS-I-1005",
    "occurrence_count": 1,
    "first_failed_at": "2026-11-11T14:02:11Z",
    "last_failed_at": "2026-11-11T14:02:11Z",
    "retry_count": 0,
    "payload_request": {"bucket": "…", "key": "…/pick_payload.json", "version_id": "…"}
  },
  {
    "PK": "FAILURE#WMS-I-1005#SO-1002#9f2c4a1b7e03",
    "SK": "META",
    "status": "FAILED",
    "failed_step": "erp_pick_confirm",
    "order_id": "SO-1002",
    "rice_id": "WMS-I-1005",
    "occurrence_count": 1,
    "first_failed_at": "2026-11-11T14:02:11Z",
    "last_failed_at": "2026-11-11T14:02:11Z",
    "retry_count": 0,
    "payload_request": {"bucket": "…", "key": "…/pick_payload.json", "version_id": "…"}
  }
]
```

All three rows point at the same S3 object: the run's pick payload is the
replayable unit for the per-order failures too — replay re-enters with the
original input plus a replay context, and convergence logic skips orders
already confirmed. Each row still carries its own pointer because rows are
independent (there is no parent lookup). Sparsity: the GSIs key on plain
attributes (`status`, `rice_id`, `order_id`, `last_failed_at`), so the global
row — no `order_id` — never appears in the per-order index, and `EFFECT#`
rows appear in none.

GSI projection right after the writes:

| Row | GSI1 `STATUS#FAILED` | GSI2 `RICE#WMS-I-1005` | GSI3 `ORDER#...` |
|---|---|---|---|
| global (`…#e4d2a90c1f55`) | yes | yes | no (sparse: no `order_id`) |
| `…#SO-1001#9f2c…` | yes | yes | `ORDER#SO-1001` |
| `…#SO-1002#9f2c…` | yes | yes | `ORDER#SO-1002` |

### 2. The API reads and lists

- Ops queue: `GET /transaction-failures` (default status FAILED) → GSI1 query,
  `ScanIndexForward=false`, `Limit=50` → page + cursor (encoded
  `LastEvaluatedKey`). All three rows above appear, newest first.
- Filtered: `?order_id=SO-1001` → GSI3; `?rice_id=WMS-I-1005&status=FAILED` →
  GSI2, status drops to a `FilterExpression`. Date range → sort-key condition
  on `last_failed_at`.
- Detail: `GET /transaction-failures/<failure_id>` → `GetItem(PK=FAILURE#<id>)`.
  **Contract unchanged**: the response carries payload *pointers*, never
  inline payload content (payloads can exceed 400 KB; inlining would break
  the schema and risk the 6 MB response ceiling). S3 retrieval happens on the
  replay path only. A presigned GET URL is an optional future addition.

### 3. Replay the stored payload

1. Trigger: `POST /transaction-failures/<id>/reprocess` (follow-up ticket;
   manual invoke until then), actor recorded as `reprocessed_by`.
2. Claim (Write paths): FAILED→RETRYING with lease, fence, budget. A
   concurrent claim loses to ConditionalCheckFailed → 409 (scenario 7).
3. Load: `GetItem` + S3 fetch of `payload_request`; the integration's
   deserializer rebuilds the request model.
4. Re-execute with the replay context. For the global row above
   (`failed_step=publish_fulfillment_pick_event`): skip ERP confirm entirely,
   then the fine-grained `EFFECT#` check decides what publishes (scenario 5).
5. Outcome — success: fenced stamp to RESOLVED, `ttl = now+90d`. The row
   leaves the GSI1 FAILED partition (appears under RESOLVED) and expires when
   the TTL fires; the sweeper then deletes its payloads.

### 4. The same failure happens again (reopen)

A month later `SO-1001` fails ERP confirm again with the same defect:

- The record/reopen upsert finds the RESOLVED row (condition passes):
  `status=FAILED`, `last_failed_at=now`, `occurrence_count+1`, latest payload
  pointer, `REMOVE ttl`, `retry_count=0`. The row re-enters the GSI1 FAILED
  ops queue automatically, and the stream transition (RESOLVED→FAILED) fires
  the ticket guard.
- If the row is mid-replay (RETRYING) — or muted (IGNORED), or dead (DEAD):
  the condition fails → the conditioned evidence-only fallback refreshes
  evidence without touching status. The writer never fights a running replay
  and never un-mutes a triaged row.

### 5. Was this payload already sent? — record and check an effect

The payload's identity already exists: the SO processor computes
`sha256(org-ship_set-fr_ids-event_timestamp)` per event group and uses it as
the SQS FIFO `message_deduplication_id`. Same payload → same sha, on every
run and every replay. The ledger turns that sha into permanent memory.

Write path (after every successful send):

1. Send succeeds, returns a MessageId.
2. `PutItem EFFECT#WMS-I-1005#publish_fulfillment_pick_event#<sha>` with
   `attribute_not_exists(PK)` — attributes `completed_at`, `tracking_id`,
   `reference` = the MessageId. A condition failure means someone already
   recorded it: a no-op.
3. Order matters: record-after-send. The inverse (record first, e.g. a
   PENDING marker) can suppress an event forever if the send then dies.

Read path (before every send): one `BatchGetItem` (`ConsistentRead=true`)
over all candidate `EFFECT#` keys. Present → skip + log. Absent → send, then
the write path.

Honest guarantee: **at-least-once effects, at-most-once records.** The
conditional put bounds *record* duplication, never *effect* duplication, and
the check-then-act gap has two windows:

- **Concurrent runs** (both check absent, both send): milliseconds.
- **Crash between send and record**: the ledger says "not done" until the
  next run — minutes to hours. FIFO dedupe absorbs redelivery only inside its
  5-minute window; past it, the duplicate delivers.

So the load-bearing control for cross-crash duplicates is **consumer-side
idempotency** (e.g. OMG's `DedupeLambdaProcessor` DEDUPE# gate) — a stated
dependency, verified per downstream before an integration adopts the ledger.
The ledger still shrinks the practical duplicate window from days to the
crash window: sequential retries, replays, and redeliveries are fully covered.

This closes the initial issue in all three of its shapes:

- **Live duplicate delivery** (WMS re-sends hours later, past the FIFO's
  5-minute dedupe window): vetoed by the batch-get.
- **Partial send + replay**: a run that published 2 of 3 groups before dying
  leaves a failure row saying "publish failed" — the batch-get skips the 2
  that went out and only the 3rd republishes (scenario 6).
- **Support lookup** ("the lab says it never arrived"): `GetItem` on the sha
  → `completed_at` + MessageId, or absent = never sent. (A GSI on `reference`
  for reverse lookups is deferred — Open decisions.)

### 6. Effect ledger closes the partial-send hole

A run publishes 3 event groups; 2 sends succeed, the 3rd raises:

- After each successful send: `PutItem EFFECT#…#<sha>` with
  `attribute_not_exists(PK)` — first writer wins, `reference` = MessageId.
- The global failure row records `publish_fulfillment_pick_event` — but 2 of
  3 events did go out. `failed_step` alone cannot see that.
- Replay (or a live duplicate delivery): batch-get the 3 shas → 2 present →
  skip → only the 3rd publishes, then its own `EFFECT#` item is written.
  Without the ledger, all 3 republish.

### 7. Two replays race the same row

Both claims are the same conditional claim (`status = FAILED`): one commits,
the other gets ConditionalCheckFailed → 409. If the winner crashes mid-replay,
the row sits in RETRYING with `retry_claim` + `claim_expires_at`; once the
lease is an hour old, the next claim's condition steals it — and the crashed
replay's fenced outcome stamp can no longer land (its `retry_claim` no longer
matches), so a zombie never overwrites the new owner's state.

### 8. Stream consumers stay failure-scoped

Every write above fires the table stream. The ESM filter (`PK` begins
`FAILURE#` ∧ `NewImage.status IN [FAILED, DEAD]`) keeps `EFFECT#` writes and
non-actionable transitions from invoking the ticket consumer; the transition
guard drops recurrence noise server-side. TTL REMOVEs carry no NewImage and
are filtered upstream. Cutover ordering is in Migration.

### 9. A status update moves the row across index partitions **(Ticket B)**

The ops-queue index keys on the plain `status` attribute, so every status
change moves the row between index partitions automatically, in the same
write — there is no duplicated index field to keep in sync.

The claim from scenario 3, as one `UpdateItem`:

```text
SET       status = :retrying,
          retry_claim = :claim_ulid, claim_expires_at = :lease_epoch,
          last_retry_at = :now, retry_count = retry_count + :one
CONDITION status = :failed OR (status = :retrying AND claim_expires_at < :now_epoch)
```

Item before → after:

```json
{ "status": "FAILED",   "retry_count": 0 }
{ "status": "RETRYING", "retry_count": 1, "retry_claim": "01J…", "claim_expires_at": 1763319602, "last_retry_at": "2026-11-11T15:40:02Z" }
```

DynamoDB deletes the old `status = FAILED` index entry and inserts the new
one in the same write — the row leaves the ops queue the moment a replay
claims it.

## Migration sketch **(Ticket B)**

Facts this plan is built on (verified against the deployed module +
the repo): the legacy table's identity formula is
`rice#order#sig12` / `rice#sig12`; its writer never flips status
(`if_not_exists`); the deployed legacy table has TTL *enabled* on attribute
`ttl` and a NEW_AND_OLD_IMAGES stream, but **no writer ever sets `ttl`**, so
no row ever expires and no consumer is attached to the stream (OEH tickets
are created inline in the event handlers).

1. **Create the state table** (infra-terraform, all envs) + IAM on the Lambda
   role + the versioned S3 payload prefix with its lifecycle safety net.
2. **Dual-write in legacy semantics** behind a flag: the new-table writer
   mimics `if_not_exists` (status never flips), so shadow verification
   compares like-for-like. Reads stay on the old table.
3. **Backfill open rows**: FAILED, DEAD, and IGNORED with status preserved
   (IGNORED included — the mute must survive migration); RETRYING backfilled
   as FAILED (legacy rows hold no valid lease; this also sidesteps the
   missing-attribute condition wedge). Convergent condition:
   `attribute_not_exists(PK) OR last_failed_at < :legacy_value`, re-putting
   full legacy state — re-runnable and repairs dual-write skew. RESOLVED rows
   are not backfilled; they die with the old table at decommission.
4. **Cut reads** to the new table. API contract unchanged; cursor format
   changes (v1 cursors rejected with 400 — in-flight pagination sessions
   break at cutover; release note, optionally a grace window that restarts
   v1 cursors from page 1).
5. **Cut writes + semantics**: stop dual-write; the new-table writer switches
   to the real conditions (reopen, fallback, flips).
6. **Stream cutover**: create the new ESM **disabled**; in the same release,
   enable it at `LATEST` (or `AT_TIMESTAMP` = the flag-flip instant) and
   disable the inline ticket-creation path. Never `TRIM_HORIZON` — that
   replays the entire dual-write history as fresh FAILED events (mass
   duplicate tickets). Consumer idempotency keyed on `failure_id` +
   transition is a stated requirement.
7. **Decommission** the old table after a soak: export to S3, then delete.
   Its RESOLVED rows never expired (TTL enabled but never written), so they
   die with the table — no row-level cleanup needed.

## Open decisions for the table ticket

- Final table name (`-state` vs `-domain`).
- Retry budget value (suggest 5 per episode) and the DEAD escalation channel.
- Support-lookup GSI on `EFFECT#.reference` (MessageId → incident): defer
  until the support-consumers conversation lands; addable online.
- Sibling correlation id source (drives a correlation GSI when the replay
  ticket needs it).
- Presigned payload URLs on the detail route (contract-preserving addon).

## Relationship to in-flight work

- **Ticket A unblocks OTCM-138123 PR4a.** PR4a's publish ledger is the first
  `EFFECT#` instance (`EFFECT#WMS-I-1005#publish_fulfillment_pick_event#<sha256>`).
  Sequencing: Ticket A ships the table (infra-terraform) plus the generic
  `EffectLedgerReader` / `EffectLedgerStore` ports and adapters (monocle);
  PR4a then wires the WMS-I-1005 publish gate to them. No FAILURE machinery
  is needed — the ledger is key-based only.
- The replay-lifecycle follow-up ticket's writer/reprocess design assumes
  `FAILURE#` rows and the claim/stamp write paths above — all Ticket B.
