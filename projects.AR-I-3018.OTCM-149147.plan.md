# OTCM-149147 — AR-I-3018: keep selecting pairs after creation dates fall behind the last run

**Plan APPROVED 2026-10-20** (user: "plan go!") · **D1 CONFIRMED**: lookback X = 5 minutes · **FSD sync APPROVED** (ran 2026-10-20)

**Ticket**: https://warbyparker.atlassian.net/browse/OTCM-149147 · **RICE**: AR-I-3018 · **Repos**: `oracle-integration-cloud` (DM window fix) + `monocle_integrations` (zero-balance skip visibility — user decision 1B, 2026-10-20) · no OIC flow change

## Context

AR-I-3018's scheduled OIC run (every 10 min) selects a credit memo + open invoice pair only when the run's window — last run date to now — covers the invoice's or memo's `ra_customer_trx_all.creation_date`. The window moves forward on every scheduled run whether or not the pair was selected. A pair that no run selected while its creation date was inside the window is never selected again, even though the memo is still unapplied and the invoice still has a balance.

**Root cause, verified on stage (2026-10-19/20):** the report inner-joins the payment-schedule (open-balance) row from `ar_payment_schedules_all`, which a background accounting process creates LATER than the header. Invoice-side lag: median 212s, avg 228s, max 3.6h (~35% of new-invoice pairs strand on first pass against the 600s window). Memos: ≤29s. Ticket example confirmed: invoice 18024 header 19:59:23, balance row 20:03:26 — the 20:00 window covered the header date but the join found no row; every later window starts past the header date. All 23 pairs in today's stage backlog carry this exact cross-boundary fingerprint.

**Also verified:** `UpdateLastRunDate` never runs on a monocle fault (orchestration-verified in the `.iar`: fault → catch → rethrow skips it) — AC3 is already met structurally; consecutive windows overlap (pointer = run-start time, written before the report's to-time); all relevant date columns are TIMESTAMP(6) on both pods, and the current query already compares TIMESTAMP to `CAST(:P AS DATE)` — no new type risk.

**User constraint (verbatim, 2026-10-20):** "we are NOT going to change the way window works, this is a proven pattern and it is used by everyone in this repo." The last-run window mechanism stays.

## The solution (F-A + lookback) — panel-verified

Window the report on the **open-balance row's creation date** instead of the header's. The balance row's creation IS the first moment the pair can be selected (the join cannot see the pair before that row exists), so a pair not yet visible in one run is necessarily picked up by a later window — the race that stranded 18024 cannot happen. Plus a **lookback** on the window's lower bound (`:P_FROM_DATE − X`) covering the residual seconds-scale race (row stamped before a run boundary, committed after the read). Re-reads are harmless: already-applied pairs are excluded by the existing `NOT EXISTS … display='Y'` check.

Verified by a 3-seat independent panel (all converged on this family) and a 2-seat adversarial panel (both ADOPT WITH CHANGES; changes folded — see "Verification panel record").

### Exact change (single data model, `WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM`)

1. `pay_sched` CTE — add the aggregate:

```sql
WITH pay_sched AS (
    SELECT
        customer_trx_id,
        class,
        SUM(amount_due_remaining) AS amount_due_remaining,
        -- The first open balance row's creation: the moment this trx became selectable.
        MIN(creation_date) AS first_open_creation_date
    FROM ar_payment_schedules_all
    WHERE class IN ('INV', 'CM')
        AND amount_due_remaining <> 0
    GROUP BY customer_trx_id, class
),
```

`MIN`, not `MAX`: it answers "when did this trx FIRST carry an open balance". `MAX` would let a later installment spuriously re-window an old pair (installments share creation stamps; zero counter-evidence in 90 days).

2. `credit_memos` CTE — project `ps.first_open_creation_date` so the predicate can use the memo side.

3. Window predicate — swap the basis, keep the lookback on the lower bound only; the `:P_TRX_NUMBER` bypass and every other predicate stay byte-identical:

```sql
AND (
    (
        :P_FROM_DATE IS NOT NULL AND :P_TO_DATE IS NOT NULL
        AND (
            (
                aps.first_open_creation_date >= CAST(:P_FROM_DATE AS DATE) - 5/1440
                AND aps.first_open_creation_date <= CAST(:P_TO_DATE AS DATE)
            )
            OR (
                cm.first_open_creation_date >= CAST(:P_FROM_DATE AS DATE) - 5/1440
                AND cm.first_open_creation_date <= CAST(:P_TO_DATE AS DATE)
            )
        )
    )
    OR (
        :P_TRX_NUMBER in(rcta.trx_number, cm.trx_number)
        AND (:P_EXCHANGE_ORDER_REFERENCE IS NULL OR cm.ct_reference = :P_EXCHANGE_ORDER_REFERENCE)
    )
)
```

(`5/1440` = 5 minutes — D1 below.) No CAST on the column: the existing code already compares TIMESTAMP columns to `CAST(:P AS DATE)` the same way.

4. Header comment rewrite in the same PR (the sentence "the creation date of the invoice or the memo falls inside it" becomes false): window on the open-balance row's creation, either side; the lookback; ad hoc date ranges now filter on balance-row creation; `:P_TRX_NUMBER` bypass unchanged.

5. Re-export the `.xdm.catalog` so the pair lands together (repo rule).

### Consequences

- Final SELECT list unchanged → `.xdo` layout, report viewers, and the monocle reader's row mapping unaffected; monocle is the only programmatic consumer.
- Contract tests unaffected (only window-exercising case is `@pytest.mark.skip`-ped; all live cases use the `P_TRX_NUMBER` bypass).
- No selection regression: falsification probe on stage (2026-10-20) — pairs selectable today but dropped under the new basis = **0**.
- Ad hoc date-range runs now mean "balance-row created in range (plus 5-min lookback)" — one line in the header; harmless for manual recovery (wider is safer).
- Worst case for a pair selectable today: selected one 10-minute window later (balance-row creation ≥ header creation but for millisecond truncation — worst observed backdate 1 ms in 90 days, absorbed by the 5-minute lookback).

### What is deliberately NOT in scope (user directives, 2026-10-20)

- **No OIC flow change.** The `UpdateLastRunDate` hardening (trx-number / date-range ad hoc runs can move the pointer; casing mismatch between routers) stays deferred — "this is a flow everyone uses." (OI-3 of OTCM-143188 keeps its own follow-up.)
- **No managed backlog drain.** Old stranded records are recovered by manual ad hoc runs anytime — "we could manually run anytime."
- **Monocle change IN scope for one item (user decision 1B, 2026-10-20)**: zero-balance skip visibility (Tony's ask 1) — supersedes the earlier "no monocle change" directive for this item only. The DM window fix itself remains report-only.
- **Unapply-revival stays manual** (a revived pair has all-old dates; auto-reapply would fight a deliberate human unapply). Documented on the ticket; confirmed by Tony ([comment 971887](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971887)); the automatic variant (memo-side last-update OR-term, mechanics + noise numbers verified by the panels) is parked as a follow-up pending functional sign-off.
- **Zero-balance skip: no re-pairing, ever** (Tony, 971887 — the skipped memo's remainder belongs to an AR-I-3019 refund). **Visibility is IN scope** (user decision 1B, 2026-10-20): one Error-severity Jira ticket per skipped memo; the run still returns 201 and the pointer advances (mechanism in "Open items from Tony's Q4 answer" item 1). The DM window fix itself is unchanged by Tony's answer.

## Stages and PRs

Two PRs — the DM window fix (PR 1) and the zero-balance skip visibility (PR 2, added 2026-10-20 per user decision 1B). Independent of each other: different repos, no shared artifacts, same Jira ticket.

| # | Proposed title | Repo | Contents | Est. lines | Depends on |
|---|---|---|---|---|---|
| 1 | `[OTCM-149147] AR-I-3018: keep selecting unapplied exchange credit memos after creation dates fall behind the last run` | oracle-integration-cloud | `BI Publisher Reports/Custom/WP Integrations/FIN/Data Model/WP_AP_AR_CREDIT_MEMO_UNAPPLIED_DM.sql` (items 1–4 above) + re-exported `.xdm.catalog` | ~25 changed + binary catalog | Base: `OTCM-136241-ar-i-3018-update-integration-with-a-5th-step` (#1064's branch — #1134 merged into it 2026-10-19); DM freshness gate at PR time; merges at prod promotion |
| 2 | `[OTCM-149147] AR-I-3018: make zero-balance credit-memo skips visible` | monocle_integrations | `_credit_memo_application.py` (+ steps/ports as designed): one Error-severity Jira ticket per skipped memo via the existing `wp_error_ticket_creation` path, dependency injected into the orchestrator; run still returns 201; colocated unit tests (100% coverage gate) | ~200 (≈40% code / 60% tests) | Independent of PR 1; full monocle PR workflow (fast checks, self-review, panel, slow suites before push) |

**Sequencing notes:**
- PR 1 live-first workflow (repo convention): edit the query in the BIP editor on **dev1** → run T1/E1/T7 (dev1 portions) → export the catalog → commit both files → open the PR per `pr-workflow` → paste to **stage** → run the stage scenarios (T1–T6, E1–E4; T3 last) → post evidence → merge at prod promotion (bundled with the #1064 stack).
- **PR 1 progress 2026-10-20**: freshness gate passed (main moved — #1139/#1132, DM untouched; only #1064 touches the DM among 71 open PRs; dev1 == stage == #1064 branch modulo BIP framing). Exact 4-hunk text authorized by the user; dev1 paste DONE via `catalog_upload.py` (`updateObject` true, re-download byte-identical; invariant found: the CDATA content equals the repo `.sql` byte-for-byte). Dev1 verification ALL PASS on existing data — T1: invoice 51326/memo 35038 family (header 01:00:25, first-open 01:03:58): balance-row-only window [01:03:00, 01:04:30] selects the trio, header-only window [00:59:00, 01:01:00] returns zero; E1: from = T+4min selects, T+6min returns zero (boundary exactly 5 min); T7-dev1 A/B (2026-07-01 → 2026-10-21): 23 identical / 0 old-only / 0 new-only / 0 value diffs. Report date params take `MM-dd-yyyy HH:mm:ss` (per the DM `<input>` declaration). Worktree `tmp/otcm149147-wt` on branch `OTCM-149147-ar-i-3018-balance-row-window` (off the #1064 branch), `.sql` applied (+16/−6), self-review clean, description drafted at `tmp/otcm149147_pr/pr_description.md`. PENDING: user re-exports the `.xdm.catalog` from dev1 (BIP UI Archive, keep permissions/timestamps) → byte-diff vs live → commit → panel review → push/open.
- PR 1 behavior changes the moment the live DM text is replaced per env — no code deploy, no feature flag. The repo PR is the reviewed backup of the live state.
- **Freshness gate before any edit:** fetch + diff `origin/main`, scan open PRs touching the DM, pull the live text from dev1 AND stage, three-way diff; the base for the edit is the LIVE text; explicit user authorization of the exact final text. Pods currently carry the post-#1134 text (= #1064 branch content).
- Prod stranding continues (~35% of new pairs) until the stack promotes; manual ad hoc recovery covers it in the meantime (user directive). State the promotion bundling in the PR description.
- PR 2 deploys on monocle's own tag pipeline, independent of the #1064 stack; note in its description that the zero-balance behavior it makes visible was introduced by OTCM-143188's row processor (same promotion train).

## Pre-PR steps

1. ~~**Jira comment on OTCM-149147**~~ — DONE 2026-10-20 (posted as comment 971868; Tony answered 971887; both-asks reply posted).
2. **FSD sync** (`integrations/sync/sync.sh --refresh --no-commit`) — APPROVED + ran 2026-10-20. Remaining: FSD Testing Strategy comparison against the new window semantics (any case asserting selection by header-creation dates flips meaning) — folds into T7.
3. ~~**Lookback value confirmation**~~ — DONE 2026-10-20 (D1 = 5 minutes, confirmed).

### Draft Jira comment — **POSTED** 2026-10-20 as [Jira comment 971868](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971868) (user-trimmed; verified by a 2-seat fact-check panel; both convergent edits applied, optionals not applied)

Verification: 2 independent seats, sentence-by-sentence against the DM SQL, monocle code, the extracted OIC flow, and stage probes — both POSTABLE WITH EDITS with the same two edits (applied below): (1) "Now," → "With the fix," — the live report still windows on the header; (2) "never gets selected" → "no scheduled window selects it again" — the ad hoc `:P_TRX_NUMBER` bypass and a future same-reference invoice falsify the absolute. Optional edits NOT applied (user's call): "Monocle skips the second memo as a success" → "…without failing the run" (seat 1); "this doesn't happen" → "this reuse doesn't happen" (seat 2). Reports: `oracle-integration-cloud/tmp/otcm149147_comment/round1/verif_{1,2}.md`.

> Update on the design.
> With the fix, the report windows on the creation date of the balance row instead of the header. The creation of the balance row is the first moment the report can select the pair. So a pair that is not visible in one run becomes visible in a later window. A lookback of a few minutes covers the commit race of a few seconds.
>
> Two cases the fix does not recover automatically:
> - A user can un-apply a memo. The pair re-opens with old dates. No scheduled window selects it again. Automatic re-application would fight a deliberate user action.
> - A zero-balance skip. Two memos can pair with the same invoice in one run. Monocle applies the first memo. The invoice balance becomes zero. Monocle skips the second memo as a success. The run returns 201. The window moves forward. No alert fires. That memo stays unapplied with old dates, and no scheduled window selects it again. **Question for the business**: should the skipped memo re-pair with the next eligible open invoice on the same exchange reference? Or is manual handling the intended rule? In other words, can several memos of one exchange legitimately reuse the same invoice? We are assuming this doesn't happen.

<details><summary>Earlier long-form draft (STE, 2026-10-20 — superseded by the user's trim)</summary>

> Update on the design. We verified it on stage. Two review panels checked it.
>
> **Root cause, confirmed.** The scheduled window selects pairs by the creation date of the transaction header (`ra_customer_trx_all`). But the report also requires the open-balance row of `ar_payment_schedules_all`. Oracle creates that balance row later than the header. On stage, the invoice-side delay is median ~3.5 minutes, max ~3.6 hours. A pair falls through when its window closes in between. The 18024/31014 example shows this: header 19:59:23, balance row 20:03:26. At current volumes, about one third of new-invoice pairs hit this case on their first pass.
>
> **Chosen fix.** The last-run window pattern stays. The report windows on the creation date of the balance row instead of the header. The creation of the balance row is the first moment the report can select the pair. So a pair that is not visible in one run becomes visible in a later window. A lookback of a few minutes covers the commit race of a few seconds. The change is report-only (.sql + .xdm). Monocle and the OIC flow do not change. You can recover pairs already stranded with an ad hoc run at any time. We plan no mass drain.
>
> **Two cases the fix does not recover automatically:**
>
> 1. **Unapply-revival.** A user can un-apply a memo. The pair re-opens with old dates. No scheduled window selects it again. Automatic re-application would fight a deliberate user action. So revival stays manual through an ad hoc run. A follow-up ticket can add automatic re-selection if the business wants it.
>
> 2. **New finding — zero-balance skip.** Two memos can pair with the same invoice in one run. Monocle applies the first memo. The invoice balance becomes zero. Monocle skips the second memo as a success. The run returns 201. The window moves forward. No alert fires. That memo stays unapplied with old dates and never gets selected. We found this collision shape in stage data. Question for the business: should the skipped memo re-pair with the next eligible open invoice on the same exchange reference? Or is manual handling the intended rule? In other words, can several memos of one exchange legitimately reuse the same invoice?
>
> We propose to re-scope AC1 to the read-lag class. This fix eliminates that class. Cases 1 and 2 get follow-ups based on your answers. @Tony Huang

</details>

> Update on the design. We verified it on stage. Two review panels checked it.
>
> **Root cause, confirmed.** The scheduled window selects pairs by the creation date of the transaction header (`ra_customer_trx_all`). But the report also requires the open-balance row of `ar_payment_schedules_all`. Oracle creates that balance row later than the header. On stage, the invoice-side delay is median ~3.5 minutes, max ~3.6 hours. A pair falls through when its window closes in between. The 18024/31014 example shows this: header 19:59:23, balance row 20:03:26. At current volumes, about one third of new-invoice pairs hit this case on their first pass.
>
> **Chosen fix.** The last-run window pattern stays. The report windows on the creation date of the balance row instead of the header. The creation of the balance row is the first moment the report can select the pair. So a pair that is not visible in one run becomes visible in a later window. A lookback of a few minutes covers the commit race of a few seconds. The change is report-only (.sql + .xdm). Monocle and the OIC flow do not change. You can recover pairs already stranded with an ad hoc run at any time. We plan no mass drain.
>
> **Two cases the fix does not recover automatically:**
>
> 1. **Unapply-revival.** A user can un-apply a memo. The pair re-opens with old dates. No scheduled window selects it again. Automatic re-application would fight a deliberate user action. So revival stays manual through an ad hoc run. A follow-up ticket can add automatic re-selection if the business wants it.
>
> 2. **New finding — zero-balance skip.** Two memos can pair with the same invoice in one run. Monocle applies the first memo. The invoice balance becomes zero. Monocle skips the second memo as a success. The run returns 201. The window moves forward. No alert fires. That memo stays unapplied with old dates and never gets selected. We found this collision shape in stage data. Question for the business: should the skipped memo re-pair with the next eligible open invoice on the same exchange reference? Or is manual handling the intended rule? In other words, can several memos of one exchange legitimately reuse the same invoice?
>
> We propose to re-scope AC1 to the read-lag class. This fix eliminates that class. Cases 1 and 2 get follow-ups based on your answers. @Tony Huang

## QA test scenarios (requirement-traceable; we execute, QA verifies; evidence per `jira-qa-evidence`)

Every acceptance criterion maps to at least one scenario. Report-only scenarios use ad hoc date parameters — no Oracle writes. "OIC monitoring" = the instance timestamps in the OIC console: the from-date of consecutive runs proves the pointer's state when the ATP pointer table is not readable by us.

### Requirements matrix (AC1–AC7)

| # | Req | Scenario | Setup / data (pod) | Run mode | Expected result | Evidence artifact |
|---|---|---|---|---|---|---|
| T1 | AC1 | Basis proof, report-only: a window covering ONLY the balance-row creation date selects the pair; a window covering ONLY the header creation date does not | Fresh seeded pair (stage, `ar-i-3018-credit-memo-test-data` skill); record the header and balance-row creation timestamps | Report, ad hoc dates | Selected in case 1, absent in case 2 — pairs whose header dates fall behind the pointer are selected by construction | Both report outputs + the timestamp record |
| T2 | AC1, AC2 | Boundary straddle, end-to-end: seed so the header lands just before a scheduled-run boundary (balance row just after) | Fresh seeded pair (stage), timed to the last minute of a 10-min cycle; schedule active | Organic scheduled runs | Run N does not select (row not yet visible); run N+1 (or N+2) applies the pair — a pair missed by one run is applied by a later one, including the import-during-run case. Timing is best-effort; T1 is the deterministic proof. Structural backstop: pointer = run-start, verified in the `.iar` | OIC run timestamps + application id + schedule balances |
| T3 | AC3 | Failed-run recovery: force a row failure, verify the pointer freezes, then fix the data and verify a later run applies the pair | Seeded pair made invalid — both ATTRIBUTE7/8 populated → monocle 500 (stage). Run LAST, in a controlled window, cleanup ready (fix data or manual apply): a failing pair blocks the schedule until fixed | Organic scheduled run (fails) → fix data → next run | The failed run 500s; the next run's from-date equals the failed run's from-date (pointer frozen, read from OIC monitoring; wiring-verified in the `.iar` — catch → rethrow skips `UpdateLastRunDate`); after the fix, a later run applies the pair | OIC instance timestamps + error notification + application id |
| T4 | AC4 | Applied pair not re-selected; hand-applied memo not selected | `TestTPCOLA04` (left applied) and the ticket's hand-applied pair 18024/31014 (stage) | Report, window + lookback covering both | Zero rows — the applied check filters overlap re-reads and hand applications | Report output (empty) |
| T5 | AC5 | Gates: a non-OMG-source memo and a zero-due (ATTRIBUTE7/8 null/zero) OMG memo are never selected | Existing classified rows from the OTCM-143188 regression buckets (stage), or query-located equivalents | Report, covering window | Zero rows for both classes — predicates byte-identical | Report output (empty) |
| T6 | AC6 | Ad hoc paths: trx-number (+ exchange reference) selects regardless of dates; a date-range run selects by balance-row creation; an `Adhoc_Run='Y'` submission does not move the pointer | Fixture pair (stage) | OIC ad hoc runs with `'Y'`; report ad hoc dates | Pair selected in each mode; consecutive scheduled-run from-dates unchanged (OIC monitoring). Note: the default-`'N'` pointer hazard stays as-is per the user directive (shared flow) — the scenario uses the correct flag | OIC timestamps + report outputs |
| T7 | AC7 | FSD Testing Strategy comparison + catalog/live parity + full A/B regression | FSD synced (Pre-PR step 2); edited DM pasted to dev1, then stage | Each FSD case mapped; byte-diff the exported catalog against the live paste; live vs edited query over the same wide window on both pods | Every FSD case passes or is re-derived in writing; catalog byte-matches the paste; edited ⊇ live, every extra row classifies as the read-lag class, zero value diffs (mirrors OTCM-143188's A/B proof) | Comparison table + diff hashes + A/B row sets |
| T8 | Tony ask 1 (971887) | Zero-balance skip visibility, end-to-end: two memos of one exchange share one invoice; the replacement total drops below the memos' sum after the memos exist | Seeded insured multi-memo exchange (stage): ATTRIBUTE7 customer memo + ATTRIBUTE8 insurance memo on one invoice, invoice total lowered after memo creation | Organic/ad hoc run (PR 2 deployed to stage) | The first memo applies; the second is skipped; the run returns 201; exactly one Error-severity Jira ticket names the skipped memo, the invoice, and the exchange reference; the pointer advances; the next run does not re-select the pair | Ticket id + application id + report output + OIC timestamps |

### Design-derived edges (from the analysis and the panels)

| # | Req | Scenario | Setup / data (pod) | Run mode | Expected result | Evidence artifact |
|---|---|---|---|---|---|---|
| E1 | D1 | Lookback boundary: `from = T + 4 min` selects; `from = T + 6 min` does not (T = the pair's balance-row creation) | T1's pair (stage) | Report, ad hoc dates | Boundary exactly at 5 minutes | Both report outputs |
| E2 | basis swap | Stray-pair falsification, re-run after the stage paste: pairs selectable under the old basis but dropped under the new | stage | Read-only SQL probe | 0 — matches the pre-change probe of 2026-10-20 | Probe output |
| E3 | D2 | MIN-guard: no result row depends on a later installment's creation stamp | T7's A/B row sets (both pods) | Read-only query | No multi-row schedules in the results, or identical stamps | Query output |
| E4 | adv F8 | Pointer-table cardinality: one `WP_INT_GENERIC_REPORT_PARAM` row per RICE_ID (`GetLastRunDate` filters RICE_ID+INTEGRATION_NAME, `UpdateLastRunDate` RICE_ID only) | stage — only if ATP is readable by us (the reporting user gets ORA-00942); else skip with a note | Read-only query | 1 row | Query output |

Full-regression note: T2 doubles as the end-to-end control; the monocle apply path is untouched, so no monocle suites are re-run for this PR (oracle-integration-cloud CI runs the title check + CodeQL only).

## Decisions

- **D1 — lookback X = 5 minutes — CONFIRMED 2026-10-20 (user, at plan approval).** The residual race is the insert→commit lifetime (seconds); 5 minutes gives ~two orders of magnitude of margin at zero cost (the overlap re-reads a handful of already-applied rows per run, filtered by the applied check).
- **D2 — `MIN(creation_date)`, not MAX, not last_update.** MIN = first moment of open balance. Invoice-side `last_update` is touched by every receipt application (122 INV + 33 CM schedule-row updates/day on stage) — a last_update window would re-fail poison pairs every 10 minutes and flood `wp_error_ticket_creation` (adversarial probe).
- **D3 — revival stays manual (Tony confirmed); zero-balance skip never re-pairs** (Tony, 971887: remainder belongs to an AR-I-3019 refund). Skip visibility IN scope (user decision 1B, 2026-10-20): one Error-severity ticket per skipped memo — not Warning (the daily `WP_PROCESS_TICKETS` auto-rejects warnings), not a 500 (the pointer must advance for every other pair). The skip fires exactly once per memo (the pair strands after the skip run), so no ticket repeats.
- **D4 — no OIC / monocle / drain companions** (user directives, verbatim in "Questions — response history" below).
- **D5 — stack on #1064's branch** (`OTCM-136241-ar-i-3018-update-integration-with-a-5th-step`); #1134 merged into it 2026-10-19. Live pods carry the post-#1134 text; freshness gate re-runs at PR time.

## Open items from Tony's Q4 answer (2026-10-20, [comment 971887](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971887))

Tony's answer does not change the DM window fix. It adds two asks and closes the pairing question.

1. **Zero-balance skip visibility (Tony ask 1) — DECIDED 2026-10-20 (user: "1B"): absorbed into OTCM-149147 as PR 2 (monocle), mechanism = Error-severity ticket per skip. Answer POSTED to Tony 2026-10-20** — he also got an open "(error level?)" sub-question; if he asks, the basis is the mechanism below / D3: the daily `WP_PROCESS_TICKETS` sweep auto-rejects Warning tickets, Error tickets survive. Today `CreditMemoZeroBalanceError` is collected into the 201 body — invisible in practice. Requirement: a skipped memo must be visible, so it does not sit unapplied forever. Skips are rare-but-real: they happen only when the replacement total drops after the memos were raised (tax/benefit adjustment); a normal multi-memo exchange drains to $0 exactly on the last memo, no skip. Mechanism options weighed:
   - **Error-severity Jira ticket per skip (CHOSEN)**: visible, not auto-rejected, and exactly one ticket per skipped memo — the pair strands after the skip run, so nothing repeats. Best fit for "at least visible".
   - **Warning response + Warning ticket**: `WP_PROCESS_TICKETS` auto-rejects Warning tickets daily — visible only until the daily job runs. Weak.
   - **Record in the `transaction_failures` table**: the strategic home, but the table/API/UI program is still landing (OTCM-139191 / 139192 / 139193) — coupling to it delays visibility. Candidate migration target later.
   - NOT an option: failing the run (500) — the skip is final (no re-pair, per Tony), and a 500 freezes the pointer and blocks the schedule for every other pair.
2. **AR-I-3019 selection check (Tony ask 2) — ANSWERED 2026-10-20 (2 independent agents converged; all claims re-verified): NO — AR-I-3019 does not select a never-applied memo. Reply POSTED 2026-10-20** (posted text below; per the posted claim, the details + both findings went to Gabriel Viera for the follow-up ticket — draft FINAL below, still not opened in Jira). Its BIP DM (`WP_AP_AR_CREDIT_MEMO_APPLIED_DM.sql:53-54`) requires `amount_due_remaining < 0` AND `amount_due_remaining > amount_due_original` (strict); a never-applied memo has remaining == original and fails the gate even when named via `P_CREDIT_MEMO_NUMBERS`. No application-table join, no attribute gates — "applied" is inferred from balance movement only. Reader: monocle `OracleCreditMemoAppliedReader` runs `WP AP AR Credit Memo Applied Report`; entry `POST /ar/credit-memo-processing`; the OIC scheduled flow is open [PR #1125](https://github.com/WarbyParker/oracle-integration-cloud/pull/1125) (OTCM-142123, not promoted). Live freshness verified (agent 2 pulled both pods): dev1 + stage carry the same predicates; the repo is ahead only in date-branch NULL guards (undeployed OTCM-114232). **Consequence: skipped remainders never close in Oracle today** → follow-up ticket needed; ask 1's per-skip ticket is the interim record. Adjacent gap (agent 2): AR-I-3019's schedule also windows on memo `creation_date`, not application date — late partial applications of old memos are missed too (same stranding shape as AR-I-3018; fold into the follow-up). Design caution: a `>=` flip would refund fresh memos AR-I-3018 hasn't applied yet (10-minute race); the predicate must target the skip case (e.g. never-applied + exchange invoice at zero balance). Reports: `oracle-integration-cloud/tmp/otcm149147_ar_i_3019/round1/agent_{1,2}.md`. **Reply to Tony: draft below, pending user review.**

   Reply POSTED by Luis 2026-10-20 (exact posted text; it carries one added open sub-question to Tony — "(error level?)" — answer basis if he asks: Error severity, because the daily `WP_PROCESS_TICKETS` sweep auto-rejects Warning tickets but not Error tickets — see item 1 mechanism / D3):

   > @Tony Huang Thanks. We will keep the creation-date window fix already in progress. Two answers follow.
   >
   > Adding to this ticket: each skipped memo will open one Jira ticket (error level?). The run still returns success and the selection window moves on, so other pairs are never blocked. The memo is never re-paired — its remainder stays open for the AR-I-3019 refund. One skip means one ticket: after the skip run, no scheduled window selects the pair again.
   >
   > With its current query, AR-I-3019 does not select a memo that was never applied. So today no automated flow closes the skipped remainders in Oracle. I already sent the details and two related findings to @Gabriel Viera for the AR-I-3019 follow-up ticket.

   Superseded full-comment draft (kept for the record):

   > Thanks Tony — this closes the pairing question. Your answers do not change the creation-date window fix already in progress. Two answers follow.
   >
   > **Ask 1 — skip visibility: agreed, and we have added it to this ticket's scope.** Each skipped memo will open one Jira ticket at Error severity, so the daily ticket sweep does not auto-reject it. The ticket names the skipped memo, the invoice, and the exchange order reference. The run still returns success and the selection window moves on, so other pairs are never blocked. The memo is never re-paired, per your point 3 — its remainder stays open for the AR-I-3019 refund. One skip means one ticket: after the skip run, no scheduled window selects the pair again.
   >
   > **Ask 2 — AR-I-3019 selection: no — with its current query, AR-I-3019 does not select a memo that was never applied.**
   >
   > Its report keeps only memos whose open credit balance has already shrunk: `amount_due_remaining < 0` and `amount_due_remaining > amount_due_original` (strict). A memo that was never applied keeps its full original balance, so it is excluded — even when the memo number is passed to the report directly. The strict balance predicates are the same in the repo and on both pods (dev1 and stage), and no open PR changes this query today.
   >
   > So today no automated flow closes the skipped remainders in Oracle. The per-skip ticket from ask 1 becomes the record of each skipped memo until this is fixed. We propose a follow-up to extend AR-I-3019's selection so these remainders get refunded as you described. One design note for it: opening the gate to every open memo would also pick up fresh memos that AR-I-3018 has not applied yet. The query has no source restriction, so manual credit memos would come along too. The predicate has to target the skip case specifically, for example never-applied OMG exchange memos whose invoice is already at zero balance.
   >
   > Two related findings from the same look:
   >
   > 1. AR-I-3019's scheduled flow also windows on the memo creation date, not on the application date. A memo applied late can be missed the same way as in AR-I-3018. We will fold this into the follow-up.
   > 2. AR-I-3019's scheduled OIC integration is still on PR #1125 (not promoted). That PR adds the schedule and the lookup row only; it does not change the selection query. The selection fix can land before or with its go-live.

   Ask-2-only reply variant: dropped after posting (the posted text above is canonical; the 6-agent-verified ask-2 text survives inside the superseded draft).

   Round-2 panel (3 independent agents, own GitHub scans + 2 own live-pod pulls): all POSTABLE (agent 1 required the C3/C4 rewords — applied; agents 2–3 POSTABLE with the same items optional). C1–C9 SUPPORTED. Open-PR scan (verified by all 3): no open PR in either repo touches the applied DM, `_wp_ar_i_3019_credit_memo_processing`, or `OracleCreditMemoAppliedReader`; deceptive candidates cleared by file list — OIC #1064 (UNAPPLIED DM = our PR 1 base), #1136 (AR-I-3018 IAR 01.01.0000), #1139 (AP-I-3006 refund DM), monocle #2777 (RMCS-I-3002), #2776/#2773 (AP-I-3006 refund reader/announcements). Round-1 panel (pre-scan draft, superseded but consistent): all POSTABLE / POSTABLE-WITH-EDITS; its required edit (predicate-not-query-text) was already in round 2, and verifier 1 added the no-source-gate design-note point — applied to the final text. Team notes for the follow-up ticket (not for the comment): (a) live pods lack the repo's `IS NOT NULL` parameter guards (repo ahead, undeployed OTCM-114232) — the edit base for the selection fix is the LIVE text; (b) the one-ticket-per-skip mechanism's operative gate is the unapplied DM's invoice positive-balance requirement; the creation-date window is the backstop; (c) PR 2 dedup edge — an ad-hoc `:P_TRX_NUMBER` run bypasses the window and can re-fire a skip on the same memo (second ticket); acceptable for deliberate re-runs, note it in the ticket; (d) PR #1125 currently `mergeable_state: dirty` (conflicts) — resolve at promotion time.

   **AR-I-3019 follow-up ticket — FINAL, HANDED OFF 2026-10-20 (user decision: Gabriel Viera creates the Jira ticket himself; the text below is his input material). Merged 2026-10-20 from 3 independent drafts: mine + 2 agents; convergence: all load-bearing content identical across the three — both hazards, both findings, evidence, artifact hygiene. Absorbed from the agents: purpose line, terms line, Finding 1/2 gap structure, "state the deltas in the PR" AC, #1125 sequence note, suggested fields. Kept from mine: double-refund guard AC, behavior-preservation AC (agent 2 lacked it), promotion-order neutrality (agent 2's "land before the schedule activates" overstated — an early #1125 promotion is harmless).**

   Summary: AR-I-3019: select and refund never-applied exchange credit memos stranded by the zero-balance skip

   Suggested fields: project OTCM, issue type Story, priority High. Rationale: a skipped memo is a refund owed to the customer, and nothing selects it today.

   Terms: memo means credit memo. Open balance means amount_due_remaining. Original amount means amount_due_original.

   Context
   - AR-I-3018 applies OMG exchange credit memos to the replacement invoices that share their exchange order reference (ct_reference). An exchange can raise several memos on one invoice. Multi-tender returns raise one memo per receipt. An insured exchange adds an ATTRIBUTE8 insurance memo beside the ATTRIBUTE7 customer memo.
   - Normally the last memo drains the invoice to $0. Sometimes the replacement total drops after the memos are raised (a tax or benefit adjustment). The invoice then reaches $0 early, and AR-I-3018 skips the remaining memo. Per OTCM-149147 (comment 971887), a skipped memo must never re-pair. Its remainder belongs to an AR-I-3019 refund.
   - AR-I-3019 exists to refund the leftover open credit of an applied credit memo. monocle exposes it at POST /ar/credit-memo-processing and refunds -amount_due_remaining per selected row.
   - OTCM-149147 makes the skip visible (one Jira ticket per skipped memo). This ticket makes AR-I-3019 close the remainder.

   The gap
   Finding 1 — the balance gate excludes never-applied memos.
   - AR-I-3019's report (WP AP AR Credit Memo Applied Report, DM WP_AP_AR_CREDIT_MEMO_APPLIED_DM) keeps only memos whose open credit balance has already shrunk: amount_due_remaining < 0 AND amount_due_remaining > amount_due_original (strict).
   - A never-applied memo has remaining == original, so it fails the strict gate. This holds even when the memo number is passed to the report directly.
   - The DM has no application-table join and no source or attribute gates. "Applied" is inferred from balance movement only.
   - Result: today no automated flow closes a skipped memo's remainder in Oracle.

   Finding 2 — the selection window uses the creation date.
   - The scheduled flow windows on the memo creation date, not on the application date. A memo applied late falls out of the window (same stranding shape as AR-I-3018 in OTCM-149147). Choose a window basis that cannot strand records behind the last run. Mirror the OTCM-149147 approach.

   Evidence (verified 2026-10-20)
   - The strict predicates are identical in the repo and on both live pods (dev1 and stage).
   - No open PR changes this query. PR #1125 (OTCM-142123) adds only the scheduled flow and the lookup row. It does not touch the DM and is currently in conflict.
   - The live pods lack the repo's IS NOT NULL parameter guards (repo is ahead, undeployed OTCM-114232). The edit base for this change is the LIVE text, per the freshness gate.
   - AR-I-3018 runs every 10 minutes on its OIC schedule.

   Design constraints
   - Do not simply relax the strict gate (>=). A fresh exchange memo passes that gate from creation, and AR-I-3018 applies within ~10 minutes. AR-I-3019 would refund the full open balance first.
   - The predicate must target the skip case: a never-applied OMG exchange memo whose same-reference invoice sits at zero balance. Add the missing restrictions: OMG batch source, the applied check (no current application), and the zero-balance same-reference invoice.
   - The refund amount is the memo's full open balance (-amount_due_remaining). That matches the remainder money-services already paid the customer.
   - A refunded memo must leave the selection (its balance closes), so no run refunds it twice.

   Scope
   - DM query change (WP_AP_AR_CREDIT_MEMO_APPLIED_DM) plus the paired .xdm.catalog re-export in the same PR.
   - The change must work whether PR #1125 promotes before or after it. Coordinate with OTCM-142123.

   Out of scope
   - AR-I-3018 skip visibility (OTCM-149147 PR 2).
   - Unapply-revival automation (parked pending functional sign-off).
   - monocle changes (reader, refund action, entry point).

   Acceptance criteria
   1. Skip case selected: a never-applied OMG exchange memo whose same-reference invoice is at zero balance appears in the report, in scheduled mode and when named ad hoc.
   2. Race guarded: a fresh exchange memo whose invoice still carries a positive balance never appears.
   3. Non-skip memos excluded: manual credit memos and non-OMG sources never appear, even when never applied.
   4. Today's behavior preserved: partially applied memos (balance moved, still open) are selected exactly as before. Fully applied memos stay excluded.
   5. Refund correctness: AR-I-3019 refunds exactly the memo's open balance, and the refunded memo never appears again on any later run.
   6. Window basis: a memo whose relevant date falls behind the last scheduled run is still selected (no stranding). An ad-hoc trx-number run selects regardless of dates.
   7. Regression evidence: A/B old-vs-new query over the same wide window on stage, every extra row classifies as the skip case, zero value diffs. Stage e2e with a multi-memo insured exchange whose second memo was skipped: the memo is selected and refunded.
   8. Artifact hygiene: the .sql and the re-exported .xdm.catalog land in the same PR. The author diffs live dev1 and live stage against origin/main and states the deltas in the PR. The edit base is the live DM text (dev1 and stage byte-identical today).

   Relations: relates to OTCM-149147 (root cause + skip visibility), OTCM-142123 / PR #1125 (scheduled flow), OTCM-114232 (undeployed repo guards). Sequence note: PR #1125 can import before this fix; until the fix lands, a scheduled run returns the current applied-memo rows only.
3. ~~**OQ1 answer upkeep**~~ — RESOLVED 2026-10-20: the posted outcome 3 reads "(a ticket will be created for visibility of these records)", which already announces the future behavior, so no repost is needed when PR 2 lands.

## Questions — exact texts and response history

### Open

(none — Q4 answered 2026-10-20; new items from Tony's response are tracked in "Open items from Tony's Q4 answer" below)

### Answered

#### Q4 — Zero-balance skip: could the invoice be reused? — **ANSWERED 2026-10-20 (Tony Huang)**

- **Context**: two memos can pair with the SAME lowest-id invoice in one run (the ranked CTE ranks per memo only). monocle's `_InvoiceBalanceTracker` drains the invoice on the first apply; the second memo raises `CreditMemoZeroBalanceError`, which is collected as a SKIP, not a failure — the run returns 201, the pointer advances, no alert fires, and the skipped memo strands invisibly. Found by the adversarial panel; code-verified; the collision shape exists in today's stage backlog (28021+28018→16062, 28022+28019→16061 — now known to be the legitimate multi-memo pattern, not test fixtures). This behavior was introduced by OTCM-143188's row processor, so its prod exposure rides the same #1064-stack promotion as this fix.
- **Question** (verbatim, posted as [Jira comment 971868](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971868)): "should the skipped memo re-pair with the next eligible open invoice on the same exchange reference? Or is manual handling the intended rule? In other words, can several memos of one exchange legitimately reuse the same invoice?"
- **Tony's answer** ([comment 971887](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971887), 2026-10-20):
  1. **Several memos of one exchange DO share one invoice, by design.** Multi-tender returns raise one customer memo per receipt; an insured exchange adds an insurance memo (ATTRIBUTE8) beside the customer memo (ATTRIBUTE7). All apply to the same replacement invoice.
  2. The amounts due on the exchange add up to the replacement invoice as placed, so the invoice should reach $0 only on the LAST memo. **A zero-balance skip means the replacement's total dropped after the memos were raised** (e.g. lower tax at collection, or a benefit adjusted after the receipt). Money-services has already refunded that difference to the customer.
  3. **The skipped memo must NOT re-pair with another invoice.** Its balance is the remainder that **AR-I-3019** should refund, as the record of that payment.
  4. **Ask 1**: monocle must not report a skipped memo as a silent success — it must at least be visible, so it does not sit unapplied forever.
  5. **Ask 2**: confirm whether AR-I-3019 selects a memo that was never applied; if not, these memos never close in Oracle.
  6. Agreed: a user un-applying a memo stays manual.
- **Response log**: 2026-10-20 — raised by adversarial seat 2; verified in monocle code and stage backlog data; posted by Luis as comment 971868; answered by Tony Huang as comment 971887 the same day. 2026-10-20 — Luis posted one reply covering both asks (exact text in open item 2 above), including an open "(error level?)" sub-question to Tony.

#### Q1 — Repeating-failure reporting (ticket's open question 1)

- **Context**: a failed run today produces error emails via the common error utility. Under any selection that retries a persistently failing pair every 10 minutes, the failure modes that survive retry (`CreditMemoRowFailedError`, abort-on-unexpected-error) spam the channel — today the sliding window eventually strands such a pair (an accidental circuit breaker).
- **Question (verbatim)**: "Is per-run error email acceptable for a persistently failing pair, or should the pair be parked after N consecutive failures (monocle-side tracking) with a single report?"
- **Proposed answer**: accept per-run notification for this ticket; name park-after-N as a follow-up if the team wants it.
- **Where to ask**: Jira comment on OTCM-149147 tagging Tony Huang.
- **Response log**: 2026-10-20 — user (chat): "Q1: acceptable, they need to fix invalid data first." → Answered; no Jira routing needed; park-after-N dropped.

#### Q2 — Unbounded vs fixed lookback (ticket's open question 2) — SUPERSEDED by user redirect

- **Context**: unbounded eligible set measured at 22–23 pairs on stage/dev1; the ticket proposed dropping the date predicate entirely.
- **Question (verbatim)**: "Unbounded open-state selection, or a fixed lookback (last run − N days from a lookup)?"
- **Response log**: 2026-10-20 — user (chat, verbatim): "you are being too narrow minded, the root cause is that the window can advance even if not all records were 'selected', so we could propose other approaches, e.g. using othe field, running again and again until all records are 'selected' (processed?) … Q2 is a game changer, we are NOT going to change the way window works, this is a proven pattern and it is used by everyone in this repo, so review again, it affect others like A2. So, first lets solve the issue with window dates and unapplied credit memos bc of the window already passed, then we will run the Assumption/Objections/suggestions again." → Question superseded: the window mechanism stays; the design task became "solve stranding inside the window pattern". Resolved 2026-10-20 as F-A + lookback (this plan) after the two-round panel.

#### Q3 — OI-12's typed search-criteria union: revive now or keep parked?

- **Context**: OI-12 (parked 2026-10-15) proposed a union of narrow request types if a third selection mode ever appeared; the pre-redirect design (unbounded mode) was that third mode.
- **Question (verbatim)**: "implement the union now … or keep the flat request + one field?"
- **Proposed answer**: keep the flat request + `all_open: bool = False`.
- **Where to ask**: internal design call.
- **Response log**: 2026-10-20 — user (chat): "Q3: flat request + one field (as every other integration does in this repo)". Mooted the same day: the chosen fix needs NO monocle change at all — no third mode, no contract change. OI-12 stays parked.

#### Directives (2026-10-20, user, chat — recorded verbatim; they replaced plan items)

- "Step 7: that doesnt matter to us, old records could be manually executed! companion 1 is not needed (this is a flow everyone uses) companion 2 not needed either (we could manually run anytime)" → OIC pointer-gate companion DROPPED; managed backlog drain DROPPED.
- "Step 8: 1. add that to the plan, when opening the ticket (description) or as a comment" → revival decision documented on the ticket (draft comment above).
- "2. that is a game changer, so two memos pair with the same invoice, and one invoice is skipped, then business-side related: could this invoice be reused ?" → became Q4.
- On the residual race: "this could be solved by using a lookback (-X minutes, I dont think a transaction could be more for 1 minute there!)" → lookback added (D1).

### Ticket open questions (from the description) — answers

The ticket carries two open questions of its own. **Answers recorded 2026-10-20** (living documents — update here first, then re-post if they change): OQ2 approved verbatim by the user ("good answer, keep it"); OQ1 built per user direction ("respond with which fails trigger an exception and which not; check the OIC integration") and verified by a 3-agent independent panel (all claims re-verified at element level; reports `oracle-integration-cloud/tmp/otcm149147_oq_verify/round1/`). **Both POSTED 2026-10-20** (user-trimmed; exact posted text in "Answer draft" below). Note: Tony's Q4 response ([comment 971887](https://warbyparker.atlassian.net/browse/OTCM-149147?focusedCommentId=971887)) makes zero-balance skips visible by requirement — the posted outcome 3 already announces it ("a ticket will be created for visibility of these records").

#### Ticket OQ1 (verbatim)

"A pair that fails on every run (for example a refused application) would be retried every 10 minutes. Does the common error utility open an OTCM error ticket per failed run? If so, how should a repeating failure be reported once?"

Answer basis (verified 2026-10-20 against `WP_AR_I_3018_CRED_MEMO_APPL_01.00.0000.iar` and `01.01.0000`, the common-error chain `.iar`s, and the monocle code):

Exception path (monocle 500 → OIC `catch` → `throw` past `UpdateLastRunDate` → global `catchAll` → `InvokeCommonError` = `WP_COMMON_ERROR_UTIL_INT`; pointer frozen → retried next run):
- **Refused application** (the ticket's scenario): SOAP apply `completed=False` → `CreditMemoRowFailedError` (`_credit_memo_row_processor.py` 236–243) → collected → `FailedCreditMemoApplicationsError` after the row loop (`_credit_memo_application.py` 107–108, 144–146) → 500. Other rows in the run still process.
- **Invalid row data**: both dues populated / no due amount / unparseable amount or date → `CreditMemoInvalidAmountError`/`ValueError` wrapped in `CreditMemoRowFailedError` (`_credit_memo_row_processor.py` 228–232) → same 500 path.
- **Unexpected error** (transport failure, bug, Oracle down): aborts the batch immediately → `CreditMemoApplicationError` → 500 (`_credit_memo_application.py` 109–127).
- **Report read failure**: reader error before any row → `CreditMemoApplicationError` → 500 (`_credit_memo_application.py` 70–72).

No-exception outcomes (201 → pointer moves → no ticket, no retry):
- **Zero-balance skip** (`CreditMemoZeroBalanceError` → collected, `_credit_memo_application.py` 103–106) — the Q4 case.
- **Duplicates** removed by the deduplicator (logged only).
- **Already-applied / ineligible pairs** — filtered by the report, never reach monocle.

Where the ticket actually comes from (3-agent independent verification 2026-10-20, reports `oracle-integration-cloud/tmp/otcm149147_oq_verify/round1/`; all claims re-verified against primary sources):

- **The ticket comes from monocle, not from OIC.** Every 500 response of the REST API is produced by the exception handlers in `_api/_handlers/_exception_handlers/__init__.py`; the catch-all `(Exception)` handler and most typed handlers are wrapped in `AtlassianTicketHandlerDecorator` (`_base_exception_handlers.py` 191–249), which calls `wp_error_ticket_creator` on every 500 with `instance_id = aws_request_id` (unique per run). `FailedCreditMemoApplicationsError` / `CreditMemoApplicationError` have no specific mapping → catch-all → ticket. **One OTCM ticket per failed run, ~144/day for a chronically failing pair.**
- **OIC deliberately stays out for this error code** (both `.iar` versions, verified at element level): the REST-fault `catch tc0` rethrows with `errorCode = VAR_WMS_WO_OUTBOUND_CREATION_ERROR`, assigned the literal `'CreditMemoApplicationError'` (`processor_227` expr; the variable name is a WMS copy-paste). The global catchAll's router route to `InvokeCommonError` carries the condition `errorCode != VAR_WMS_WO_OUTBOUND_CREATION_ERROR` (`processor_330/output_332/resourcegroup_339/expr.properties`) → **no OIC email, no OIC ticket, no exception-log insert for monocle 500s** — just a faulted instance. The throw also skips `UpdateLastRunDate` → pointer frozen → same window retried next run.
- Common error utility (when other flows DO invoke it; extracted `/tmp/err_util_1000`, `/tmp/err_util_1003`): **01.00.0000** = emails per DVM flags + `InsertErrorLogsIntoDB` (ATP `WP_EI_EXCEPTION_LOG_PACKAGE` → `WP_INT_EXCEPTION_LOG`); **01.00.0003** = 8 typed routes invoking `WP_COMMON_ERROR_TICKET_CREATI|01.00.0000` → monocle `wp_error_ticket_creation` (one Jira ticket per error). AR-I-3018 calls 01.00.0003 only on the UpdateATPScope-failure path. DVM row for AR-I-3018: InterfaceError/ImportError/EmailNotification = Y; Success/NoFile = N.

No dedup (verified): monocle `WpErrorTicketCreator.__call__` generates the template and creates the ticket unconditionally — no existing-ticket search, and every title/body carries the unique AWS request id; `WpProcessTickets` (daily, via OIC `WP_PROCESS_TICKETS`) only rejects warning tickets. A stay-eligible refusal (invalid data) therefore opens one ticket per run, every 10 minutes, until fixed. A refusal that also removes eligibility (invoice paid by hand meanwhile) stops by itself.

User direction (2026-10-20): answer says which fails raise the exception and which not; then yes, a ticket per failed run; "right now, there is no way to avoid creating a ticket that was created before, this is being worked on failures_table related tickets". The failures-table program exists and is active: `transaction_failures` DynamoDB table — OTCM-138121 / 138128 / 138131 / 138133 (done), OTCM-139191 / 139192 / 139193 (read API + OMG-UI, in progress).

#### Ticket OQ2 (verbatim)

"Unbounded open-state selection or a fixed lookback: which does the Oracle team prefer for the report's cost on the production pod?"

Answer basis: neither — the chosen design keeps the bounded last-run window and changes only the date basis (balance-row creation) plus a minutes-long lookback, so the report's prod cost is today's cost (same tables/joins, one added aggregate in an already-grouped CTE, ~15-minute window instead of ~10). Unbounded selection scans the full eligible set every run; a days-long lookback re-reads days of rows and still strands older pairs.

#### Answer draft — **POSTED** 2026-10-20 (user-trimmed; exact posted text)

> @Tony Huang Regarding the open questions:
>
> Open Question #1. A report row has four outcomes: (1) Applied: returns 201. (2) Refused or invalid: returns 500. (3) Zero-balance skip: returns 201 (a ticket will be created for visibility of these records). (4) Duplicate or ineligible: the run returns 201. An unexpected error, for example Oracle going down mid-run, aborts the batch at once and also returns 500.
>
> Every 500 opens one OTCM ticket. The ticket comes from monocle's own API error handling, not from the OIC common error utility. So a pair that fails on every run opens a ticket on every run. Right now there is no way to avoid creating a ticket that was created before. This is being worked on in the failures-table related tickets.
>
> Open question #2. Unbounded selection or a fixed lookback (report cost on prod).
>
> Neither. We keep the bounded window and only change the date it checks: the creation date of the balance row, not the header, plus a lookback of a few minutes. The prod cost stays the same as today: same tables and joins, one added aggregate, a window of about 15 minutes instead of 10. The two proposed alternatives cost more and fix less. An unbounded open-state read scans the full eligible set every 10 minutes. A days-long lookback re-reads days of rows every run and still strands pairs older than the lookback. The balance-row basis avoids both, and it removes the stranding by construction: a pair that is not visible in one run becomes visible in a later window.

Superseded longer draft (kept for the record):

> Answers to the ticket's open questions.
>
> **Open question 1 — a pair that fails on every run (refused application).**
>
> First, which fails raise the exception and which do not. A report row has four outcomes:
>
> 1. **Applied.** The application completes. No exception.
> 2. **Refused or invalid — raises the exception.** Oracle refuses the application (`completed = false`), or the row carries invalid data: both due amounts populated, no due amount, or an unparseable amount or date. The row fails. The run still processes the other rows. It returns 500 after the loop.
> 3. **Zero-balance skip — no exception.** The invoice balance is already zero, so monocle skips the memo and the run returns 201. No ticket fires. This is the case from the design comment above.
> 4. **Duplicate or ineligible — no exception.** The deduplicator drops repeated rows. The report itself filters already-applied memos and non-qualifying pairs.
>
> An unexpected error, for example Oracle going down mid-run, aborts the batch at once and also returns 500.
>
> Every 500 opens one OTCM ticket. The ticket comes from monocle's own API error handling, not from the OIC common error utility. Monocle's catch-all handler creates a ticket on every 500, with no check for an existing one. The OIC flow rethrows the failure as `CreditMemoApplicationError` and deliberately skips the common error utility for that code. It also skips the last-run update, so the next run retries the same pair. So a pair that fails on every run opens a ticket on every run. That is one ticket every 10 minutes.
>
> On reporting a repeating failure once: right now there is no way to avoid creating a ticket that was created before. This is being worked on in the failures-table related tickets.
>
> Until that lands, the mitigation is operational. A refusal caused by invalid data keeps failing until the data is fixed. A refusal that also removes the pair's eligibility stops by itself. For example, if the invoice gets paid by hand, the report no longer selects the pair, and the next run succeeds.
>
> **Open question 2 — unbounded selection or a fixed lookback (report cost on prod).**
>
> Neither. The scheduled run keeps the bounded last-run window, the same pattern the other integrations use. The change is the date the window checks: the creation date of the balance row, not the creation date of the header, plus a lookback of a few minutes. The report cost on prod stays the same as today. The query keeps the same tables and joins. It adds one aggregate to an already-grouped subquery. The window grows from about 10 minutes to about 15.
>
> The two proposed alternatives cost more and fix less. An unbounded open-state read scans the full eligible set every 10 minutes. A days-long lookback re-reads days of rows every run and still strands pairs older than the lookback. The balance-row basis avoids both, and it removes the stranding by construction: a pair that is not visible in one run becomes visible in a later window.

## Verification panel record

**Round 1 — independent convergence (3 seats, identical brief, no access to my conclusion):** all three converged on the chosen family — keep the window, fix the date basis it selects on, recover the backlog ad hoc, no monocle change. Variants offered: seat 1 a last-activity-date basis (rejected by both adversarial seats: invoice schedule rows are touched by every receipt application → poison-pair 500 spam); seat 2 an OIC-side 2-day lookback (rejected as the core: arbitrary lag boundary, standing backlog re-reads); seat 3 a hybrid (its revival arm auto-re-applies deliberate human unapplies — a business decision, parked). Reports: `oracle-integration-cloud/tmp/otcm149147_q2/round1/indep_{1,2,3}.md`.

**Round 2 — adversarial review (2 seats, my solution as-found):** both ADOPT WITH CHANGES. Folded: (1) AC1 re-scope — revival recurs forever and the zero-balance skip strands invisibly, so AC1 is honestly the read-lag class; (2) self-healing claim reworded from "necessarily" to the empirical guarantee + residual commit race (then closed by the user's lookback directive); (3) DM header rewrite in the same PR; (4) ad hoc semantic-shift documentation; (5) stacking correction — #1134 merged into #1064's branch 2026-10-19, base = live text; (6) pointer-table cardinality check folded into stage verification (`GetLastRunDate` filters RICE_ID+INTEGRATION_NAME, `UpdateLastRunDate` RICE_ID only). Rejected by the seats as core alternatives: lookback-only, last-activity basis, memo-side last_update revival arm (parked). Verified in my favor: pointer frozen on fault (AC3 already met), windows overlap never gap, backlog 100% RC1-signature, types TIMESTAMP(6) both pods, contract tests untouched, no materially backdated rows (1 ms worst, see F13 below), my own falsification probe (0 pairs lost by the basis swap). Reports: `oracle-integration-cloud/tmp/otcm149147_q2/round2/adv_{1,2}.md`.

**Cleanup**: DONE 2026-10-20. All OTCM-149147 scratch dirs (`tmp/otcm149147_q2`, `otcm149147_comment`, `otcm149147_oq_verify`, `otcm149147_ar_i_3019`, `otcm149147_tony_reply`, `otcm149147_gabriel_ticket`) and the `/tmp` `.iar` extraction dirs (`ar_i_3018_iar_*`, `err_util_*`, `err_ticket_1000`, `process_tickets_1000`) were removed post-consolidation. Report paths cited above are historical. Other tickets' scratch under `tmp/` (OTCM-146798, OTCM-143188, `ar_i_3018_dm_review`, `pr*`) untouched.

## Pre-PR review round (2026-10-20, run 20261020T1508) — panel, best-of-N fixes, dev1 re-paste

**Panel**: 4 panels × 3 seats (code, principles, linus, requirements), pre-opening mode on the branch diff (briefs deleted per rule; reports `oracle-integration-cloud/tmp/otcm149147_pr/review/round1/` until PR opens). Zero BLOCKERs, 1 SHOULD-FIX, 15 findings. User rulings 2026-10-20:

- **F1** (SHOULD-FIX) lookback rationale absent → 2-line comment above the window block (why: commit race; lower-bound-only both sides; applied check filters re-reads). APPLIED.
- **F2+F3** scope → PR-description bullet: fix is forward-looking (stranded backlog recovers manually via `:P_TRX_NUMBER`, no managed drain); Jira comment 971975 supersedes the ticket description's drop-the-predicate proposal. APPLIED. QA companion: the T1/T2 evidence comment states the AC1 re-scope (AC1's literal wording is not satisfied for the already-stranded backlog; QA tests the re-scoped reading).
- **F4** duplicate-apply race → user correction: OIC does NOT serialize scheduled instances. Race needs BOTH: pair created in the window's 5-minute overlap slice AND apply chain (OIC + monocle lambda + AR commit) uncommitted at the next run's read (~10 min). Bounded: a pair duplicates at most once, then self-heals; AR rejects the duplicate (no corruption); the error chain opens a ticket. Alternatives: 1-minute lookback REJECTED (silent stranding of batch/ESS rows committing >1 min after insert — the original bug class; trades a loud failure for a silent one); preemptive 10→20 REJECTED (latency, non-exhaustive). ADOPTED = user's option A: keep 5-minute lookback; the duplicate-apply error ticket is the recognized signal to widen the schedule (DM comment documents it). Triage of such a ticket includes a rerun check (an erroring run can leave unprocessed pairs until a manual rerun). Structural follow-up candidate for PR 2: apply-time idempotency (lambda re-checks for an existing application and skips instead of erroring).
- **F5+F9** MIN semantics → comment reworded (currently-open basis, forward-only re-anchor, installment gloss). APPLIED.
- **F6** ad hoc semantic → header comment (ad hoc range = first still-open balance-row creation, not header's; `:P_TRX_NUMBER` locates a pair). APPLIED.
- **F7** prod stamp-guard probe → rollout evidence: post-promotion, run the distinct-stamp probe on PROD (read-only; dev1/stage showed 0 distinct-stamp groups).
- **F8** record the window basis in the FSD → comment prepared; reply in the existing selection-logic thread ([Drive id AAACIoDQK4A](https://docs.google.com/document/d/18VyR76v5hXvU09rnibpgzxgHljVcZqtR/edit?disco=AAACIoDQK4A), anchor "Credit memo created from OMG is not applied to any invoice — Selection logic…") AFTER the PR opens. Prepared text in chat 2026-10-20.
- **F10** header visibility sentence → reworded (both-rows condition via the inner join; either-side windowing keeps every pair reachable). APPLIED.
- **F11** `INTERVAL '5' MINUTE` vs `5/1440` → keep `5/1440` (DATE−INTERVAL returns TIMESTAMP; type-change risk). REJECTED.
- **F12** params CTE dedup → over-DRY. IGNORED (user).
- **F13** plan wording "zero backdated rows" → false at ms precision (2 memos, 1 ms; lookback absorbs). FIXED in place (Consequences + Round-2 record).
- **F14** catalog present-perfect while pending → accepted (pre-open gate holds the claim until the re-export lands). IGNORED.
- **F15** pre-existing OIC watermark observations (two `current-dateTime()` calls, ≤seconds drift absorbed by the lookback; `UpdateLastRunDate`-on-failure statically indeterminable — covered by T3 + wiring verification) → QA evidence note.

**Best-of-N (user directive)**: 3 independent implementations of the approved comment/doc fixes (mine + 2 generalPurpose agents, same brief, no cross-visibility). All diffs verified comments-only (0 non-comment lines, ≤99 cols, lookback untouched); all three independently converged on the F4 outcome. Winner per user: **B wholesale + A's MIN comment**. Applied to the worktree `.sql`; the final branch diff = the 4 SQL hunks (window fix) + 5 comment hunks. Scratch: `oracle-integration-cloud/tmp/otcm149147_pr/bestofn/` (brief deleted per rule; candidates kept until PR opens).

**Dev1 re-paste**: DONE 2026-10-20 — rebuilt `_datamodel.xdm` (raw CDATA swap), `updateObject` on dev1, re-download byte-verified (live CDATA == worktree `.sql`, 7663 bytes). Rollback copy `/tmp/otcm149147_gate/dev1_edited/_datamodel.ORIGINAL.xdm`. Invariant codified: raw `<![CDATA[` span == repo `.sql` byte-for-byte; the `el.text` extraction path adds `\n`+12sp prefix and `\n`+9sp suffix (23 bytes). Skill updates from this: `xdm_set_sql.py` + `xdm_verify_sql.py` + a paste-round-trip section added to the `fusion-sql` skill; `drive_comment_ids.py` added to `management-open-items`.

**PR OPENED 2026-10-20**: catalog re-export placed in the worktree + T7 parity PASSED (catalog SQL == repo `.sql` byte-identical); commit `23176a6d` (`[OTCM-149147] Fix AR-I-3018 unapplied exchange credit memo selection when creation dates fall behind the last run` — verb-first per user, RICE id mid-message, `AR-I-3018:` prefix style dropped), pushed `origin OTCM-149147-ar-i-3018-balance-row-window`; PR [#1143](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143) opened against `OTCM-136241-ar-i-3018-update-integration-with-a-5th-step` (the #1064 stack), `bug` label applied, review-request message delivered in chat. Review-round scratch (`tmp/otcm149147_pr/review/`, `tmp/otcm149147_pr/bestofn/`) removed post-opening per rule; `pr_description.md` kept as the PR-body source.

**Lookback change 2026-10-20 (user directive, post-PR)**: 5 → 2 minutes, superseding the D1 X=5 confirmation. `.sql` (5 hunks) + PR description updated. Tradeoff: the F4 duplicate-apply overlap slice shrinks to 2 minutes (fewer races); a balance row committing >2 minutes after insert strands until an ad hoc run — the class the 5-minute value covered. Chain DONE 2026-10-20: dev1 re-pasted (`updateObject` true, round-trip VERIFY OK 7663 bytes, scratch `/tmp/otcm149147_2min/` with rollback `_datamodel.ORIGINAL.xdm`); user re-exported the catalog (landed in the main checkout again — moved to the worktree, main restored); PARITY OK; commit `0ebd3b24` (`.sql` + catalog together) pushed to #1143; PR body refreshed from file (label checkbox now truthfully checked). FSD comment draft updated to 2 minutes. Bugbot thread on #1064 ([date filters span two tables](https://github.com/WarbyParker/oracle-integration-cloud/pull/1064#discussion_r4317412612)) assessed: facts accurate, remedy inapplicable (OR is the either-side pair semantics; window columns are aggregate-CTE outputs, no index path to block; memo set eligibility-bounded by design) — reply drafted in chat for approval.

**Tony's review on #1143 (2026-10-20 22:25 UTC; reviewed the 5-minute commit) + user rulings (2026-10-21)** — two threads, verified first-hand by 2 independent agents (reports `oracle-integration-cloud/tmp/otcm149147_pr1143_comments/agent_{1,2}.md`). Verified facts: monocle 500 → flow catches/rethrows BEFORE `UpdateLastRunDate` → pointer freezes; pointer = run-START snapshot; "Jira item 4" = item 4 of Tony's comment 972074, conditional on item 1, precondition fails; TPP79X00Z7's ~4 min = header→balance-row creation lag (median 3.5 min, max 3.6 h on stage) — the class the basis swap absorbs; rows of one transaction stamp within 1 ms, zero backdated in 90 days; Oracle has no per-row commit timestamp. **Rulings**: Q1 = concede the header reword ("…makes each pair selectable in the window that covers the later side's balance-row creation"); Q2 = **rollback to 5 minutes**; Q3 = **option 2: BIP report parameter `P_LOOKBACK_MINUTES` default 5** — user creates the parameter in the dev1 BIP editor (catalog edits are editor-only; the paste only touches SQL CDATA); day-2 tuning = any DM editor changes the default. Sweep (daily wide-range) = follow-up gated on evidence of long transactions. Reply drafts LOCKED in `oracle-integration-cloud/tmp/otcm149147_pr1143_comments/pr_comment_replies.yaml` (thread 1: pointer-freeze evidence + header-reword concession; thread 2: stays-at-5 + parameter + OR semantics + coverage evidence + evidence-gated sweep) — post AFTER the new head lands.

**Parameterization edit (2026-10-21)**: freshness gate re-ran PASSED (origin/main DM untouched since 2026-05-22; main tip moved via #1139, other files; open-PR scan: #1142/#1140/#1141 touch other files, only #1064 touches the DM; live pulls: dev1 == worktree head byte-identical 7663 bytes, stage == #1064 base 6268 bytes). `.sql` edited in the worktree: `2/1440` → parameter on both predicates, header reword conceded, parameter documented in the header/major-changes/window comments. User directives folded the same day: (a) user does the editor work on BOTH pods (no SOAP paste by agent); (b) predicates use `CAST(:P_LOOKBACK_MINUTES AS NUMBER)/1440` so the bind is forced numeric. Editor attempt 1 (user, dev1+stage): SQL landed byte-identical on both pods (7875 B), but the parameter was created as `P_LOOKBACK_MINUTES/1440` (the `/1440` copied into the name; `defaultValue="5"`, `xsd:integer` correct) — the SQL binds `:P_LOOKBACK_MINUTES`, so the name must be exactly that. Editor attempt 2 (user, dev1+stage): ALL GREEN — both pods' live SQL == worktree `.sql` byte-identical (7907 B, CAST version), parameter `name="P_LOOKBACK_MINUTES" defaultValue="5" dataType="xsd:integer"` + `<input>` correct on both pods, worktree `.xdm.catalog` re-export parity OK (catalog SQL == repo `.sql`). **E1 boundary smoke PASSED on dev1 with the default unpassed**: report echoes `<P_LOOKBACK_MINUTES>5</P_LOOKBACK_MINUTES>`; from = T+4min (01:07:58) selected the seeded family (51326/35038, 51327/35039, 51328/35040), from = T+6min (01:09:58) returned zero — boundary exactly 5 min via the defaulted bind + CAST. **COMMITTED + PUSHED 2026-10-21**: commit `b7b290d0` (`[OTCM-149147] Make the AR-I-3018 window lookback a report parameter`, `.sql` + `.xdm.catalog`) pushed to #1143 (`0ebd3b24..b7b290d0`); PR body refreshed from `tmp/otcm149147_pr/pr_description.md` (stale "stage paste follows" line fixed — stage now carries the text + parameter). **Reply verification round (2026-10-21, 2 independent seats, word-level, reports `tmp/otcm149147_pr1143_comments/verify_round1/seat_{1,2}.md`, brief deleted per rule)**: seat 1 re-probed both pods live (0 backdated at any margin, median 3.52 min / max 213.5 min stage lag re-derived, flow re-extracted); seat 2 verified element-level from the record. Convergent SUPPORTED: pointer freeze wiring, header reword landed, parameter default 5, pointer = run-start, TPP79X00Z7 4m03s, 1 ms stamp sharing, OR/inner-join semantics, trx bypass, sweep-as-intent. Consolidated edits APPLIED to the YAML: (1) reply 1 "retries the same window" → "starts from the same date and retries its pairs" (seat 1: the frozen-pointer window extends, not repeats; seat 2 called it harmless — precision adopted); (2) reply 2 "zero backdated rows" → "no materially backdated rows" (seat 2 required per F13's 2-memo 1 ms finding; seat 1's live probe found literal zero — wording true under both adopted); (3) reply 2 "which runs sub-second here" DELETED (seat 2: unsourced — no commit timestamp exists, record says seconds-scale); (4) "does not occur" → "has not occurred" (seat 2 optional, adopted). **"Separate steps" named first-hand (2026-10-21, stage)**: `created_by`/`request_id` pulled from both AR tables for the ticket pair (18024/31014) + backlog pairs (16061/16062, 28018/28019/28021/28022); ESS requests resolved via `ess_request_history` (`definition`). Invoice side: header written by **`AutoInvoiceImportEss`** (AutoInvoice Import, submitted by `ext.vbellurkar` on stage — prod = scheduled submission); balance row written 3–4 min later by **Vertex.Taxuser** — its `PopulatePartnerLines` job (req 127928177) or an inline call (req -1) — i.e. the Vertex tax completion creates the payment schedule row. Memo side: one OAuth API client (`ec0d977d…`) writes both rows 2–4 s apart (no ESS). Different submitters + different request ids = separate processes/commits proven; the 3.5-min median lag IS the Vertex completion cadence. This backs the reply's "created in separate steps, each committed on its own".

**Replies POSTED 2026-10-21**: reply 1 ([r4336521050](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143#discussion_r4336521050)) and reply 2 ([r4336521224](https://github.com/WarbyParker/oracle-integration-cloud/pull/1143#discussion_r4336521224)), exact YAML bodies as user-trimmed (the "For clarity on selection (OR/inner-join)" paragraph was removed from reply 2 by the user pre-post; text stays on the shelf in case Tony asks). Vertex enrichment declined ("keep it as-is"). PENDING: (1) stage QA T1–T6/E1–E4 on the parameterized text; (2) FSD comment (F8); (3) Jira items 1–2 answer draft for comment 972074 (Q4 — verified answers: 500 freezes pointer; pointer = run-start); (4) merge at prod promotion bundled with the #1064 stack.

**Still pending**: user creates `P_LOOKBACK_MINUTES` in dev1 BIP editor → dev1 re-paste → catalog re-export → commit/push → post Tony replies → PR body refresh → FSD comment (F8 — draft re-presented in chat for approval; prepared text lost to context compaction) → stage paste (own confirmation) → stage QA T1–T6/E1–E4 → evidence → merge at prod promotion bundled with the #1064 stack.

## PR 2 (monocle) — pre-PR review round (2026-10-20, run 20261020T1738) + fixes applied

**Panel**: 4 panels × 3 seats on the PR-2 branch diff (13 files; briefs deleted per rule; reports `monocle_integrations/tmp/pr2_review/panels/round1/`). 18 findings consolidated. User rulings 2026-10-20 — APPLIED:

- **1** ticket traceback → dropped ENTIRELY per user improvement (`traceback=""`, SQS-DLQ caller precedent); the byte-identical boilerplate added nothing, the message already sits in the summary.
- **2** abort path → the unexpected-error branch now tickets the accumulated skips before raising `CreditMemoApplicationError` (guarded by `if zero_balance_skipped_details:`); new unit test covers it.
- **3** over-claim → closing text reworded to "Unless another invoice on the same exchange order still carries a balance, the memo stays unapplied…".
- **15C** assignment → deferral note in the Jira comment draft (shared ticket creation has no assignee support; opens unassigned at Error).
- **16** skip lines now carry business unit + open balance per memo.
- **18** Jira comment drafted (consolidated shape + rationale + assignment deferral; `<PR link>` placeholder until open).
- **4** reader `str(row.get("EXCHANGE_ORDER_REFERENCE") or "")` (None-safe).
- **8A/5/9/14/17/7/6/10** confirmed as designed: building on orchestrator stays; mixed run = two tickets (skip + error chain) correct; env-plumbing follow-up candidate; Error per Tony; no dedup accepted; concrete annotation, `typing.List`, parallel accumulators stay.

IGNORED: **13** ("remainders belong to the AR-I-3019 refund flow" kept as design intent), **12** (no deploy-order note in PR description), **11** (pre-existing kinesis bug).

**Verification**: consolidated `ZeroBalanceSkip` dataclass deleted, accumulator now holds port details directly. Scoped serial pytest 103 passed (incl. new abort test); `make format` clean (mypy strict); `make test-unit` 7292 passed. NOTE: the reader's two `_integration_test.py` tests fail under `-n auto` on the CLEAN tree too (pre-existing xdist seeding race; they run serially under `make test-integration`) — not caused by this change, not fixed here. PR description updated (BU + open balance in the ticket bullet; abort-mid-run ticketing). Slow suites (`make check-coverage`, scoped `make test-api`) still pending per pr-workflow — they run right before push.

**Gates + commit (2026-10-20)**: `make check-coverage` 100% (7292 passed); `make test-api` FULL (352 passed, 2 known skips) — full scope because `_api/_test/conftest.py` changed. Commit `14bda86da` `[OTCM-149147] Make AR-I-3018 zero-balance credit-memo skips visible` (13 code files only; `.docs/architecture/integrations.md` + `AGENTS.md` edits stay uncommitted on main per user ruling). **Push saga**: SSH hangs/resets from the agent shell (Connection reset by 140.82.113.3 port 22 after 20 min; HTTPS has no stored creds); push succeeded 2026-10-21 05:18 with fail-fast ssh options (`BatchMode`, `ServerAlive*`) — network had recovered. **GitHub MCP down ~2026-10-20 18:19 → 2026-10-21 05:22** (catalog "ready", auth "succeeds", router reports server missing; recovered on its own). **PR OPENED 2026-10-21**: monocle [#2795](https://github.com/WarbyParker/monocle_integrations/pull/2795) against `main`, body verbatim from `tmp/pr_description.md`, `enhancement` label applied, label checkbox then checked + body refreshed. Jira comment (finding 18 + 15C draft) still awaiting user confirmation; review-request message delivered in chat.

**Cleanup 2026-10-21**: removed `monocle_integrations/tmp/pr2_review/` (panel reports + branch.diff + ticket copy — consolidation done, PR open) and `/tmp/agent1_ar3018` (.iar extraction). KEPT: `monocle_integrations/tmp/pr_description.md` (PR-2 body source), `oracle-integration-cloud/tmp/otcm149147_pr/pr_description.md` (PR-1 body source), `oracle-integration-cloud/tmp/otcm149147_pr1143_comments/` (agent reports + reply YAML — Tony's threads still awaiting user rulings Q1–Q4), `oracle-integration-cloud/tmp/otcm149147-wt` (PR-1 worktree — needed if the header reword lands), the 2 uncommitted monocle doc files (user ruling: stay out of PR 2). Other tickets' tmp scratch untouched.

## Jira comment 972074 reply (2026-10-21) — benchmark + 3-seat verification, draft ready

**STAGE FACT CHANGE (verification-caught, all 3 seats converged)**: TPP79X00Z7 was APPLIED on stage 2026-10-19 20:54:06 UTC (application 377956, memo 31014 → invoice 18024, 395.00, both schedules CL) — ~2 days BEFORE the parameterized DM landed on stage, so by hand or ad hoc (applier not probed). The AC's equivalent-pair fallback now governs the stage evidence: the ad hoc drain demonstrates on pairs still stranded at QA time, and an equivalent stranded pair covers the scheduled-run leg.

**OTCM-149784 filed** = the AR-I-3019 never-applied selection follow-up (handed to Gabriel 2026-10-20 with full text; filed by 2026-10-21 ~09:00). Linked in the comment's item 6.

**Benchmark (independent agent, 30/30 runs OK, `oracle-integration-cloud/tmp/otcm149147_jira_comment/timing_benchmark_report.md`, per-run XML `/tmp/otcm149147_bench/`)**: live report via `run_bip_report.py` (byPassCache, same call OIC makes), medians — dev1: 1d 0.8 s / 1m 0.9 s / 1y 0.9 s; stage: 1d 1.0 s / 1m 1.0 s / 1y 0.9 s; worst 1.7 s (two tied cold starts, stage 1d r1+r2). Caveat: 1y returns the same 23 rows as 1m (no older unapplied memos) — wide window stresses the date scan, not volume.

**Verification round (3 independent seats, reports `tmp/otcm149147_jira_comment/verification/seat_{1,2,3}_report.md`, briefs deleted per rule; draft snapshot + Tony's comment + ticket description preserved there)**: ~25 findings deduped, ALL APPLIED per user ruling 2026-10-21: 7–8 rewritten for the TPP79X00Z7 application; "console change, not a data-model edit" → "parameter-default change in the BIP console, not a query edit" (scheduled path never passes the parameter — the budget IS the DM-stored default); "insert-to-commit delay, which takes seconds" → commit-lag framing + memo side measured 0–3 s (seat 2: one API client writes both rows; invoice side ~3.5 min systematic over 10 recent invoices, import user vs Vertex.Taxuser); "longest run" sub-ask acknowledged (OIC instance durations not pulled — moot under start-recording); "one skip opens exactly one ticket" → one consolidated ticket per run naming every skip (PR #2795 body confirms); "daily ticket sweep" → "ticket sweep" (cadence unevidenced; Warning-only auto-reject verified); 1.7 s "slowest single run" → "slowest runs" (tie); prod-size caveat re-added ("these pods are smaller than prod, the largest our access can time"); item 6 = handoff date + OTCM-149784. KEPT per user wording: §1 "(The dedup of repeated failure tickets belongs to the failures-table tickets.)" (no artifact by that name — reference to the OQ1-thread dedup program). Verified clean: all flow mechanics, all numbers, default-5 echo + re-pass-60 both pods, verbatim AC quote, PR #2795 open at `14bda86da`.

**A/B re-checker note (seat 2)**: "23 identical / 0 value diffs" reproduces only against the pre-149147 deployed text (`git show 23176a6d^:...sql`); `origin/main` is still pre-143188 (0 identical / 21 value diffs against it — expected, not a regression).

**Atlassian MCP degraded 2026-10-21 ~08:50–09:05** (3 timeouts on getJiraIssue; the Jira search at ~07:15 worked). Workaround used: local ticket sync `tickets/OTCM-149147/` (comments.json `body_md` + description.adf.json) for Tony's comment text.

**POSTED 2026-10-21 ~09:20 ET** (by the user, with final trims from the verified draft). The tmp file `comment_972074_reply.md` now holds the exact as-posted text; the pre-post verified draft survives as `verification/draft_under_review.md`. User's final trims: numbered bold headers dropped (plain paragraphs); §2 dropped the run-length/benchmark sentence, the OIC-durations mootness line, and the memo-side 0–3 s sentence; §3 dropped the benchmark-method sentence, the 23-row volume caveat, the prod-size caveat, and the dev1/stage bold (the A/B sentence was already dropped by the user pre-verification); §6 dropped the Gabriel handoff date; §7–8 dropped the explicit TPP79X00Z7-applied-10-19 disclosure and the Adhoc_Run='Y' drain sentence (the equivalent-pair phrasing retained, so stage QA T2 stays governed by the AC fallback — but note Tony was NOT told the pair is already applied; the QA evidence comment should name it when it lands). Kept as verified/applied: OR-criteria pipeline-gap sentence (added pre-post per user), parameter-default-not-query-edit, consolidated-ticket granularity, "ticket sweep" (no "daily"), 1.7 s tie wording, OTCM-149784 link.

**PENDING**: Tony updates description/ACs per his items 1–2 → stage QA T1–T6/E1–E4 (T2 uses the equivalent-pair fallback; the ad hoc drain runs on remaining stranded pairs; the evidence comment names the 10-19 TPP79X00Z7 application) → FSD comment (F8) → PR-2 Jira comment (consolidated shape + assignment deferral — draft to re-create from this plan) → sweep follow-up gated on evidence.
