# Decisions

Consolidated decision log — newest first. Day files capture context in the
moment; this file is the searchable record for reviews, leveling evidence, and
"why did we do X?".

One entry per decision:

### YYYY-MM-DD — short title
- **Decision**: what was decided
- **Why**: context, alternatives rejected
- **Links**: Jira key, PR, Slack thread

---

## 2026

### 2026-09-29 — Auto-commit the notes vault daily
- **Decision**: `sync.sh` + launchd agent `com.ioet.notes-sync` commit and push
  the vault every day at 18:00; `passwords.kdbx` is gitignored, not backed up.
- **Why**: the remote was only updated when I remembered to push; these notes
  feed standups and weekly reviews, so losing them is not acceptable. Secrets
  stay out of the auto-commit on principle.
- **Links**: [[README]] (auto-sync section)
