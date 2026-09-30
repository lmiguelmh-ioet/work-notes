#!/usr/bin/env bash
# sync.sh — daily auto-commit for this notes vault: stage everything, commit as
# "update <ISO timestamp>", pull --rebase, push to origin. Run by launchd
# (com.ioet.notes-sync) or manually. Log: .cache/sync.log
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
mkdir -p .cache

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
