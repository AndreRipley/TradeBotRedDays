#!/bin/bash
# Complete git sync and push script

cd /Users/andreripley/Desktop/TradeBot

echo "=========================================="
echo "Git Sync and Push Script"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "❌ Error: Not a git repository"
    exit 1
fi

# Show current status
echo "📋 Current git status:"
git status --short
echo ""

# Add all changes
echo "📦 Adding all changes..."
git add -A
echo ""

# Show what will be committed
echo "📝 Files staged for commit:"
git status --short
echo ""

# Check if there are changes to commit
if git diff --cached --quiet && git diff --quiet; then
    echo "ℹ️  No changes to commit"
else
    echo "💾 Committing changes..."
    git commit -m "Add Cloud Run deployment support with health check endpoint

- Added HTTP health check server for Cloud Run compatibility
- Created deployment scripts for Google Cloud Platform
- Added environment variable documentation
- Updated main.py to include health check endpoint on port 8080
- Created deploy_fix_permissions.sh for automated deployment
- Added CLOUD_RUN_ENV_VARS.md guide"
    echo ""
fi

# Pull remote changes first
echo "📥 Pulling remote changes..."
if git pull origin main; then
    echo "✅ Pull successful"
else
    echo "⚠️  Pull had issues. Continuing anyway..."
fi
echo ""

# Push changes
echo "📤 Pushing to GitHub..."
if git push origin main; then
    echo ""
    echo "=========================================="
    echo "✅ Successfully pushed to GitHub!"
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "❌ Push failed. Check the error above."
    echo "=========================================="
    exit 1
fi

