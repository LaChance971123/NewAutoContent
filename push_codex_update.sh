#!/bin/bash

echo "🔄 Syncing Codex updates with GitHub..."

# Ensure we're on main
git checkout main || { echo "❌ Failed to switch to main"; exit 1; }

# Pull latest
git pull origin main || { echo "❌ Failed to pull latest from main"; exit 1; }

# Stage all changes
git add .

# Commit with timestamp
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
git commit -m "Codex update @ $TIMESTAMP" || echo "ℹ️ Nothing to commit."

# Push to origin/main
git push origin main || { echo "❌ Push failed"; exit 1; }

echo "✅ Codex changes successfully pushed to main!"
