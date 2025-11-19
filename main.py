import os
import json
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from aiogram import Bot, Dispatcher
from aiogram.types import Message, Update
from aiogram.filters import Command

import boto3
from supabase import create_client

# Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is required")

STORAGE_MODE = os.getenv('STORAGE_MODE', 'local')  # local | s3 | supabase

# S3 settings
S3_BUCKET = os.getenv('S3_BUCKET')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')
S3_REGION = os.getenv('S3_REGION', 'us-east-1')

# Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_BUCKET = os.getenv('SUPABASE_BUCKET', 'books')

# Webhook host (use your Fly app URL)
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST')  # e.g. https://tender-render-ready.fly.dev
PORT = int(os.getenv('PORT', '8080'))

uploads_dir = os.path.join(os.getcwd(), 'static', 'files')
os.makedirs(uploads_dir, exist_ok=True)

META_FILE = os.path.join(os.getcwd(), 'files.json')
if not os.path.exists(META_FILE):
    with open(META_FILE, 'w') as f:
        json.dump([], f)

def save_meta(entry: dict):
    with open(META_FILE, 'r+') as f:
        data = json.load(f)
        data.append(entry)
        f.seek(0)
        json.dump(data, f, indent=2)

def list_meta():
    with open(META_FILE, 'r') as f:
        return json.load(f)

# Initialize clients
s3_client = None
if STORAGE_MODE == 's3' and AWS_ACCESS_KEY and AWS_SECRET_KEY:
    s3_client = boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=S3_REGION
    )

supabase = None
if STORAGE_MODE == 'supabase' and SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Admin list
ADMIN_IDS = os.getenv('ADMIN_IDS', '')
ADMIN_IDS = [int(x) for x in ADMIN_IDS.split(',') if x.strip().isdigit()]

@dp.message(Command('start'))
async def cmd_start(message: Message):
    await message.reply("Assalomu alaykum! Kitob yuklash uchun fayl yuboring. Adminlar /list_files bilan ko'rishi mumkin.")

@dp.message()
async def any_message(message: Message):
    if not message.document:
        return
    doc = message.document
    filename = doc.file_name or f"file_{doc.file_id}"
    local_path = os.path.join(uploads_dir, filename)

    await message.bot.download(document=doc, destination=local_path)

    uploaded_url = None
    if STORAGE_MODE == 's3' and s3_client:
        s3_client.upload_file(local_path, S3_BUCKET, filename)
        uploaded_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{filename}"
    elif STORAGE_MODE == 'supabase' and supabase:
        with open(local_path, 'rb') as f:
            supabase.storage.from_(SUPABASE_BUCKET).upload(filename, f, {"upsert": True})
        res = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(filename)
        if isinstance(res, dict):
            uploaded_url = res.get('publicURL') or res.get('public_url') or str(res)
        else:
            uploaded_url = str(res)
    else:
        uploaded_url = f"/files/{filename}"

    meta = {
        "file_name": filename,
        "uploader_id": message.from_user.id,
        "storage": STORAGE_MODE,
        "url": uploaded_url
    }
    save_meta(meta)

    await message.reply(f"📚 Yuklandi! Saqlash: {STORAGE_MODE}\nURL: {uploaded_url}")

@dp.message(Command('list_files'))
async def cmd_list_files(message: Message):
    if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
        await message.reply("Siz admin emassiz.")
        return
    data = list_meta()
    if not data:
        await message.reply("Hali hech qanday fayl yuklanmagan.")
        return
    text = "\n".join([f"{i+1}. {d['file_name']} — {d['url']}" for i,d in enumerate(data)])
    await message.reply(f"Fayllar:\n{text}")

app = FastAPI()
env = Environment(loader=FileSystemLoader('templates'), autoescape=select_autoescape(['html','xml']))

app.mount('/static', StaticFiles(directory='static'), name='static')

@app.on_event('startup')
async def on_startup():
    if WEBHOOK_HOST:
        webhook_url = f"{WEBHOOK_HOST}/webhook/{BOT_TOKEN}"
        await bot.set_webhook(webhook_url)
        print('Webhook set to', webhook_url)
    print('Startup complete.')

@app.post('/webhook/{token}')
async def webhook_handler(token: str, request: Request):
    if token != BOT_TOKEN:
        raise HTTPException(status_code=403, detail='Invalid token')
    data = await request.json()
    update = Update(**data)
    await dp.process_update(update)
    return {'ok': True}

@app.get('/', response_class=HTMLResponse)
async def index():
    tmpl = env.get_template('index.html')
    files = list_meta()
    return HTMLResponse(tmpl.render(files=files))

@app.get('/files/{filename}')
async def serve_file(filename: str):
    local = os.path.join(uploads_dir, filename)
    if os.path.exists(local):
        return FileResponse(local, filename=filename)
    data = list_meta()
    for d in data:
        if d['file_name'] == filename:
            return RedirectResponse(d['url'])
    raise HTTPException(status_code=404, detail='File not found')

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=PORT)
