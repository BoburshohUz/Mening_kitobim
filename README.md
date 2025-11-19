# tender_render_ready — Telegram Book Upload Bot

This repository contains a full Telegram bot (webhook-driven) with:
- aiogram (webhook)
- FastAPI web UI
- Local / Amazon S3 / Supabase Storage support
- Fly.io deployment config and scripts
- GitHub Actions workflow for auto-deploy

## Quickstart

1. Copy `.env.example` to `.env` and fill values (BOT_TOKEN, WEBHOOK_HOST, etc.)
2. (Optional) Run `scripts/setup_s3.sh` or `scripts/setup_supabase.sh` to create buckets
3. Set Fly secrets (or use `scripts/deploy_fly.sh`)
4. Deploy with `flyctl deploy` or via GitHub Actions
