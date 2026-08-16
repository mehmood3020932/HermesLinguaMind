#!/usr/bin/env bash
# Clones datascale-ai/opentalking (Apache-2.0) into third_party/opentalking so
# docker-compose's `avatar` profile can build it. Not vendored/committed into
# this repo — that would bloat a "lightweight" deliverable with a whole
# separate project's source tree and model-adapter code we don't own.
#
# Run this once before: docker compose --profile avatar up --build
set -euo pipefail

REPO_URL="https://github.com/datascale-ai/opentalking.git"
TARGET_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/third_party/opentalking"
# Pin this to a specific commit before any real deployment — tracking `main`
# is fine for local trial, not for anything you'd call reproducible/production.
REF="${OPENTALKING_REF:-main}"

if [ -d "$TARGET_DIR/.git" ]; then
  echo "third_party/opentalking already present — updating to ${REF}"
  git -C "$TARGET_DIR" fetch --depth 1 origin "$REF"
  git -C "$TARGET_DIR" checkout FETCH_HEAD
else
  echo "Cloning ${REPO_URL} (${REF}) into ${TARGET_DIR}"
  mkdir -p "$(dirname "$TARGET_DIR")"
  git clone --depth 1 --branch "$REF" "$REPO_URL" "$TARGET_DIR" 2>/dev/null \
    || git clone --depth 1 "$REPO_URL" "$TARGET_DIR"  # fallback if $REF isn't a branch name
fi

echo "Done. Next: docker compose --profile avatar up --build"
