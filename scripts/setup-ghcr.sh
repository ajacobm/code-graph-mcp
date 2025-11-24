#!/bin/bash
# One-time setup for GHCR publishing

set -e

echo "🚀 Setting up GitHub Container Registry (GHCR)..."
echo ""

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) not found"
    echo "   Install from: https://cli.github.com/"
    exit 1
fi
echo "✅ GitHub CLI found"
echo ""

# Check if logged in
if ! gh auth status &> /dev/null; then
    echo "❌ Not logged in to GitHub"
    echo "   Run: gh auth login"
    exit 1
fi
echo "✅ Authenticated with GitHub"
echo ""

# Get repo info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "📦 Repository: $REPO"
echo ""

# Enable GitHub Actions workflow permissions
echo "⚙️  Configuring Actions permissions..."
echo ""
echo "Please ensure the following settings are enabled:"
echo "1. Go to: https://github.com/$REPO/settings/actions"
echo "2. Under 'Workflow permissions', select:"
echo "   ✓ Read and write permissions"
echo "   ✓ Allow GitHub Actions to create and approve pull requests"
echo ""
read -p "Press Enter once you've confirmed the settings..."
echo ""

# Check if workflow file exists
if [ -f .github/workflows/docker-publish.yml ]; then
    echo "✅ Workflow file exists: .github/workflows/docker-publish.yml"
else
    echo "❌ Workflow file not found"
    exit 1
fi
echo ""

# Trigger workflow
echo "🚀 Triggering initial build..."
gh workflow run docker-publish.yml
echo ""
echo "✅ Workflow triggered!"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ Setup complete!"
echo ""
echo "Monitor build progress:"
echo "  gh run watch"
echo ""
echo "Or visit:"
echo "  https://github.com/$REPO/actions"
echo ""
echo "Once build completes, images will be at:"
echo "  ghcr.io/$(echo $REPO | tr '[:upper:]' '[:lower:]'):sse-latest"
echo "  ghcr.io/$(echo $REPO | tr '[:upper:]' '[:lower:]'):stdio-latest"
echo "  ghcr.io/$(echo $REPO | tr '[:upper:]' '[:lower:]'):http-latest"
echo "  ghcr.io/$(echo $REPO | tr '[:upper:]' '[:lower:]'):production-latest"
echo "  ghcr.io/$(echo $REPO | tr '[:upper:]' '[:lower:]'):development-latest"
echo ""
echo "Make packages public (one-time):"
echo "  1. Go to: https://github.com/$(echo $REPO | cut -d'/' -f1)?tab=packages"
echo "  2. Click on 'codenav'"
echo "  3. Package settings → Change visibility to Public"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
