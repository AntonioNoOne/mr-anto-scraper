#!/usr/bin/env sh
set -eu

if [ ! -d ".git" ]; then
  echo "Run this from the repository root; .git not found." >&2
  exit 1
fi

git config core.hooksPath .githooks
chmod +x .githooks/pre-commit .githooks/pre-push || true
echo "Git hooks enabled: .githooks"
echo "Test with: python scripts/project_guard.py"
