#!/usr/bin/env bash
set -euo pipefail

# Squash trailing data-update commits into a single commit and publish updates.
#
# Behavior:
# - If no data changes: exit 0.
# - If HEAD is a data commit: rewrite the trailing run of data commits into one new
#   commit with the latest artifacts, then force-push with lease.
# - If HEAD is not a data commit: append a single data commit and push normally.

DATA_DIRS=("data/preprocessed")
DATA_FILES=("data/etag-map.json" "public/preprocessed/index.json")

commit_is_data() {
  git log -1 --pretty=%s | grep -Eq '^(chore\(data\):|data:)' || return 1
}

last_non_data_commit() {
  # Find the most recent commit that is NOT a data commit.
  if git rev-list -n 1 \
      --grep '^chore\(data\):' \
      --grep '^data:' \
      --invert-grep HEAD >/dev/null 2>&1; then
    git rev-list -n 1 \
      --grep '^chore\(data\):' \
      --grep '^data:' \
      --invert-grep HEAD
  else
    # Fallback to root commit if history is all data commits (unlikely)
    git rev-list --max-parents=0 HEAD | tail -n 1
  fi
}

ensure_git_user() {
  git config user.name  "github-actions[bot]" || true
  git config user.email "github-actions[bot]@users.noreply.github.com" || true
}

stage_only_data_paths() {
  local had_any=false
  for d in "${DATA_DIRS[@]}"; do
    if [ -d "$d" ]; then
      git add -A -- "$d" || true
      had_any=true
    fi
  done
  for f in "${DATA_FILES[@]}"; do
    if [ -f "$f" ]; then
      git add -A -- "$f" || true
      had_any=true
    fi
  done
  if ! $had_any; then
    echo "No known data paths exist; nothing to do." >&2
    exit 0
  fi
}

snapshot_msg() {
  printf 'chore(data): snapshot %s [skip ci]' "$(date -u +"%FT%TZ")"
}

main() {
  ensure_git_user

  # Stage only data artifacts
  stage_only_data_paths

  # If nothing staged, exit
  if git diff --cached --quiet; then
    echo "No data changes to publish."
    exit 0
  fi

  # Determine current branch name if available; default to main
  BRANCH=${GITHUB_REF_NAME:-}
  if [ -z "$BRANCH" ]; then
    # Try to infer from HEAD symbolic ref; fall back to main
    BRANCH=$(git symbolic-ref --short -q HEAD || echo main)
  fi

  if commit_is_data; then
    echo "HEAD is a data commit; squashing trailing data commits into one." 

    # Save updated artifacts aside first (since we'll move HEAD)
    TMPDIR=$(mktemp -d)
    trap 'rm -rf "$TMPDIR"' EXIT
    mkdir -p "$TMPDIR/data/preprocessed" "$TMPDIR/public/preprocessed"
    for d in "${DATA_DIRS[@]}"; do
      if [ -d "$d" ]; then
        rsync -a --delete "$d"/ "$TMPDIR/$d"/
      fi
    done
    for f in "${DATA_FILES[@]}"; do
      if [ -f "$f" ]; then
        mkdir -p "$(dirname "$TMPDIR/$f")"
        cp -f "$f" "$TMPDIR/$f"
      fi
    done

    # Find the last non-data commit to base on
    BASE=$(last_non_data_commit)
    echo "Base (last non-data commit): $BASE"

    # Move to base and recreate a single data commit with latest artifacts
    git checkout -f "$BASE"
    for d in "${DATA_DIRS[@]}"; do
      if [ -d "$TMPDIR/$d" ]; then
        mkdir -p "$d"
        rsync -a --delete "$TMPDIR/$d"/ "$d"/
      fi
    done
    for f in "${DATA_FILES[@]}"; do
      if [ -f "$TMPDIR/$f" ]; then
        mkdir -p "$(dirname "$f")"
        cp -f "$TMPDIR/$f" "$f"
      fi
    done

    stage_only_data_paths
    git commit -m "$(snapshot_msg)"

    # Fast-forward branch ref locally and push with lease
    git branch -f "$BRANCH" HEAD
    git push --force-with-lease origin "HEAD:$BRANCH"
  else
    echo "HEAD is not a data commit; appending a new data snapshot commit."
    git commit -m "$(snapshot_msg)"
    git push origin "HEAD:$BRANCH"
  fi
}

main "$@"
