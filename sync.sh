#!/usr/bin/env bash
# sync.sh — daily auto-commit for this notes vault: stage everything, commit as
# "update <ISO timestamp>", pull --rebase, push to origin. Run by launchd
# (com.ioet.notes-sync) or manually. Log: .cache/sync.log
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p .cache

# A failed run fires sound + modal (once per day) — the log alone is not a notification.
loud_failure() {
    local today
    today=$(date +%F)
    echo "$(date '+%F %T') SYNC FAILURE: $1" >> .cache/sync.log
    [ "$(cat .cache/alert_state 2>/dev/null || true)" = "$today" ] && return
    afplay /System/Library/Sounds/Glass.aiff || true
    # State is written only after the dialog displays; otherwise retry next failure.
    osascript -e "display alert \"notes sync FAILED\" message \"$1\\n\\nDetails: $(pwd)/.cache/sync.log\"" \
        && echo "$today" > .cache/alert_state || true
}
trap 'loud_failure "exit $? (line $LINENO)"' ERR

git add -A
if git diff --cached --quiet; then
    echo "$(date '+%F %T') no changes"
    exit 0
fi

ts=$(date +%Y-%m-%dT%H:%M:%S%z | sed -E 's/([0-9]{2})([0-9]{2})$/\1:\2/')
git commit -m "update $ts"
git pull --rebase
git push
echo "$(date '+%F %T') pushed: update $ts"
