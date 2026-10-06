# Work notes

Obsidian vault for work notes. Backed up to GitHub (`work-notes` repo) and
synced across work/personal devices.

## Conventions

- **Naming**: `topic.subtopic.md` — topic prefix + dot + subtopic
  (`team.oncall.md`, `projects.RMCS-I-3001.md`, `meetings.new-requirement.md`).
  A topic with a single note stays flat (`english.md`, `data.md`); when it
  grows a second note, split it into the `topic.` prefix.
- `day/` — daily notes as `day-YYYYMMDD.md`, scaffolded from `day-template.md`.
- `day/week-YYYY-Www.md` — weekly reviews; scaffold with
  `./weekly-review.py [YYYY-MM-DD]` — it collects the week's `### Stand Up`
  sections as source material (`--stdout` to preview, `--force` to overwrite).
- `decisions.md` — consolidated decision log (newest first); day files capture
  context in the moment, this is the searchable record.
- `team.1on1.<name>.md` — running 1:1 notes per person; copy
  `team.1on1-template.md`.
- `assets/` — images/attachments referenced from notes.
- `urls.md` — bookmarked links catalog (consumed by the `open-note-url` skill).

## Project notes (ticket-scoped)

Work is organized by **ticket**, not by RICE id. A ticket has a lifecycle:
open → done → frozen. Frozen files don't rot — a finished ticket file is never
edited again, so it can be trusted as history. RICE-level notes accrete across
several tickets and silently go stale; don't create them.

- **Index**: `projects.md` — one card per ticket (newest first): date · status ·
  link to the ticket file · one-line outcome. Detail lives in the ticket file,
  not here.
- **Ticket file**: `projects.<RICE>.<TICKET>.md` (e.g.
  `projects.RMCS-I-3001.OTCM-139313.md`) — RICE-first so filename search hits
  both the RICE id and the ticket key, and same-RICE tickets cluster together.
  A ticket touching several RICE ids uses the primary one in the name and lists
  the rest in the header line (content search finds them). Fixed skeleton:
  Outcome / What shipped / Decisions / Evidence / Test data / Open items /
  Artifacts. **Decisions** records who confirmed what and where (FSD comment
  date, spreadsheet, PR review) — that is the audit trail.
- **Plan archive**: `projects.<RICE>.<TICKET>.plan.md` — verbatim copy of the
  Cursor plan file at wrap-up; the frozen decision log. Never curated, never
  edited.
- **Domain knowledge lives in skills, not in ticket files.** Operational,
  cross-ticket knowledge (recipes, table cheatsheets, eligibility rules) goes
  into the matching `~/.cursor/skills/<name>/` skill — skills are living
  documents, updated on every use. Ticket files link the skill; they never
  duplicate it. Test data: point to the skill (preferred) or to the
  `integrations/<RICE>/` script/data path.
- **RICE-level archive**: old `projects.<RICE>.md` notes are renamed to
  `projects.<RICE>.archive.md` with a frozen banner. Curate-on-touch: when a
  new ticket needs something from an archive, copy that piece into the ticket
  file instead of reviving the archive.

### `projects.md` card template

One card per ticket, newest first. Every field is labeled — no positional
values ("which date is this?" is a template bug). Nothing beyond these
bullets; detail lives in the ticket file.

```markdown
## <TICKET> – <short title>
- **Ticket**: <Jira URL>
- **RICE**: <RICE id(s)>
- **Dates**: YYYY-MM-DD → YYYY-MM-DD — created → finished; open end (`→ —`) = in flight
- **Outcome**: <one line: what changed in the world>
- **Notes**: [projects.<RICE>.<TICKET>](projects.<RICE>.<TICKET>.md)
```

Exactly these five items — no PRs, no status field: those live in the ticket
file. The card is an index entry, not a summary. Older freeform cards migrate
to this template when touched.

### Ticket file template

`projects.<RICE>.<TICKET>.md` — fixed sections, in this order:

```markdown
# <TICKET> — <RICE>: <short title>
- **Ticket** / **RICE** / **Repos** / **Status** (as of YYYY-MM-DD) / **Plan** link

## Outcome      — 2-4 bullets, management-readable, past tense
## What shipped — one item per PR / deploy / tag, each with link + state
## Decisions    — two numbered lists:
                  ### Functional clarifications (Q&A): one line each —
                  question → answer (who, where, when)
                  ### Design decisions (ours): one line each + why
## Evidence     — QA runs: date, env→pod, identifier set, result;
                  Jira evidence comment id
## Test data    — where it lives: skill name (preferred) or script/data
                  path; which orders/pods exist today
## Open items   — what remains + what it is blocked on
## Artifacts    — FSD/spec links, skills touched, related notes
```

Readability rules: one PR per item; every decision numbered; every
clarification answers who/when/where; **one concept per item** — a sentence
carrying 2+ different concepts splits into sub-items; the file is frozen when
the ticket closes.

## Auto-sync (daily commit)

`sync.sh` stages everything, commits as `update <ISO timestamp>`, pulls with
`--rebase`, and pushes to `origin/main`. The launchd agent
`com.ioet.notes-sync` runs it daily at 18:00 (a missed run fires on next wake).
Log: `.cache/sync.log`. If a rebase conflict ever blocks it, resolve manually
and run `./sync.sh`.

```bash
launchctl load ~/Library/LaunchAgents/com.ioet.notes-sync.plist    # enable
launchctl unload ~/Library/LaunchAgents/com.ioet.notes-sync.plist  # disable
./sync.sh                                                          # manual run
```

Not auto-committed (see `.gitignore`): `passwords.kdbx` (secrets),
`.obsidian/workspace.json` (per-device UI state), `.cache/`.

## GIT (manual / other-device setup)

On this machine the steps below are automated by `sync.sh` (see above).

### Creating subtree

```
git remote add work-notes git@github.com:lmiguelmh-ioet/work-notes.git
git subtree push --prefix=ioet work-notes main
# authenticate as the personal GitHub account — on this machine the remote uses
# the `ioet` SSH host alias (git@ioet:lmiguelmh-ioet/work-notes.git, key ~/.ssh/ioet)
```

### On personal device

```
cd ~/notes
git add -A
git commit -m "..."
git push                                              # personal backup
git subtree push --prefix=ioet work-notes main        # work repo

# PULL: bring work-device commits back into ioet/
git subtree pull --prefix=ioet work-notes main --squash
```

### On work device

```
cd ~/notes                 # or wherever you cloned work-notes
git add -A
git commit -m "..."
git pull                   # in case parent pushed
git push                   # to work-notes
```
