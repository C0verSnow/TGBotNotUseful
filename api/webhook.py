import hmac
import json
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from bot.config import required, OperationError
from bot.handlers import handle

app = FastAPI()
logger = logging.getLogger(__name__)


@app.get("/")
def health():
    return {"ok": True}


@app.post("/api/webhook")
async def webhook(request: Request):
    try:
        secret = required("TELEGRAM_WEBHOOK_SECRET")
    except OperationError:
        return JSONResponse({"ok": False}, status_code=503)
    supplied = request.headers.get("x-telegram-bot-api-secret-token", "")
    if not hmac.compare_digest(supplied.encode(), secret.encode()):
        return JSONResponse({"ok": False}, status_code=403)
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            return JSONResponse({"ok": False}, status_code=413)
    try:
        update = json.loads(body)
        if not isinstance(update, dict):
            raise ValueError
    except (ValueError, UnicodeDecodeError):
        return JSONResponse({"ok": False}, status_code=400)
    try:
        await run_in_threadpool(handle, update)
    except Exception:
        # Never log incoming command bodies, tokens, HTTP URLs, or exception text.
        logger.error("Webhook processing failed; inspect service configuration")
        return JSONResponse({"ok": False}, status_code=500)
    return {"ok": True}
