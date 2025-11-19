#!/bin/bash
set -e
if ! command -v flyctl > /dev/null; then
  echo "Please install flyctl: https://fly.io/docs/hands-on/install-flyctl/"
  exit 1
fi
echo "Logging into Fly..."
flyctl auth login
echo "Launching app (non-interactive where possible)..."
flyctl launch --copy-config --no-deploy --name tender-render-ready || true
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
  flyctl secrets set BOT_TOKEN="$BOT_TOKEN" STORAGE_MODE="$STORAGE_MODE" ADMIN_IDS="$ADMIN_IDS" || true
  if [ -n "$AWS_ACCESS_KEY" ]; then
    flyctl secrets set AWS_ACCESS_KEY="$AWS_ACCESS_KEY" AWS_SECRET_KEY="$AWS_SECRET_KEY" S3_BUCKET="$S3_BUCKET" S3_REGION="$S3_REGION" || true
  fi
  if [ -n "$SUPABASE_KEY" ]; then
    flyctl secrets set SUPABASE_URL="$SUPABASE_URL" SUPABASE_KEY="$SUPABASE_KEY" SUPABASE_BUCKET="$SUPABASE_BUCKET" || true
  fi
  if [ -n "$WEBHOOK_HOST" ]; then
    flyctl secrets set WEBHOOK_HOST="$WEBHOOK_HOST" || true
  fi
else
  echo ".env not found; set secrets manually with flyctl secrets set"
fi
echo "Deploying..."
flyctl deploy
