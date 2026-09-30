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
git remote add work-notes git@github.com:luis-mamani-wp/work-notes.git
git subtree push --prefix=ioet work-notes main
# add a remote key
git config remote.work-notes.sshCommand 'ssh -i /home/ml/.ssh/ioet_wp -o IdentitiesOnly=yes'
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
