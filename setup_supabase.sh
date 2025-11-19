#!/bin/bash
set -e
if [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ] || [ -z "$SUPABASE_BUCKET" ]; then
  echo "Please set SUPABASE_URL, SUPABASE_KEY and SUPABASE_BUCKET."
  exit 1
fi
echo "Creating Supabase bucket (if not exists)..."
curl -s -X POST "$SUPABASE_URL/storage/v1/bucket" \
  -H "apikey: $SUPABASE_KEY" \
  -H "Authorization: Bearer $SUPABASE_KEY" \
  -H "Content-Type: application/json" \
  --data '{"name":"'$SUPABASE_BUCKET'","public":true}' || true
echo "Supabase setup done."
