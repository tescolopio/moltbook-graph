#!/bin/bash
# Git Push Script for Moltbook Knowledge Graph
# Pushes generated files to GitHub at regular intervals
# Run via cron: */5 * * * * /mnt/d/moltbook-graph/scripts/git_push.sh

set -e

REPO_DIR="/mnt/d/moltbook-graph"
LOG_FILE="/tmp/moltbook-git-push.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

cd "$REPO_DIR"

# Check if there are changes to commit
if git diff --quiet && git diff --staged --quiet; then
    log "No changes to push"
    exit 0
fi

# Add generated files
git add \
    *.png \
    *.json \
    index.html \
    interactive.html \
    last_update.txt \
    2>/dev/null || true

# Check if there's anything staged
if git diff --staged --quiet; then
    log "No staged changes"
    exit 0
fi

# Commit and push
TIMESTAMP=$(date +'%Y-%m-%d %H:%M')
git commit -m "🤖 Auto-update: ${TIMESTAMP}" >> "$LOG_FILE" 2>&1

if git push origin main >> "$LOG_FILE" 2>&1; then
    log "Successfully pushed changes"
else
    log "Push failed - will retry next interval"
    exit 1
fi
