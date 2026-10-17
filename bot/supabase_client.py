import base64
import json
import logging
import re

from bot.config import required, OperationError
from bot.http import request


logger = logging.getLogger(__name__)

def public_key():
    key = required("SUPABASE_KEY")
    if key.startswith("sb_publishable_"):
        return key
    # Legacy anon keys are JWTs. Inspect the role only to reject wrong config;
    # Supabase, not this decoding, verifies the JWT signature.
    try:
        _, payload, _ = key.split(".")
        if json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("role") == "anon":
            return key
    except (ValueError, AttributeError, UnicodeDecodeError):
        pass
    raise OperationError("SUPABASE_KEY 必须是 publishable 或 anon 公钥，不能使用私钥。")


def database(method, table, *, representation=True, **kwargs):
    key = public_key()
    # Publishable keys are not JWTs: send them as apikey, never as Bearer.
    return request(method, required("SUPABASE_URL").rstrip("/") + "/rest/v1/" + table,
                   headers={"apikey": key,
                            "Prefer": "return=representation" if representation else "return=minimal"}, **kwargs)


def claim(update_id):
    # A unique primary key makes concurrent/retried deliveries fail closed.
    try:
        response = database("POST", "bot_updates", representation=False, json={"update_id": update_id})
    except OperationError:
        # Never log credentials, URLs, exception text, or command contents.
        logger.error("Dedup claim failed: update_id=%s transport_or_configuration_error", update_id)
        raise
    if response.status_code == 201:
        return True
    try:
        body = response.json()
        code = body.get("code") if isinstance(body, dict) else None
    except ValueError:
        code = None
    # Error messages/details can contain credentials or user data. Log only
    # the machine-readable SQLSTATE/PostgREST code after validating its shape.
    if not isinstance(code, str) or not re.fullmatch(r"(?:[0-9A-Z]{5}|PGRST[0-9]{3})", code):
        code = "unknown"
    if response.status_code == 409 and code == "23505":
        return False
    logger.error("Dedup claim failed: update_id=%s status=%s code=%s",
                 update_id, response.status_code, code)
    if code in {"PGRST205", "42P01"}:
        raise OperationError("消息去重表未初始化，操作未执行。请管理员在 Supabase SQL Editor 运行 migrations/005_bot_updates.sql；已建表时请检查 SUPABASE_URL 和 API schema 缓存。")
    if code == "42501":
        raise OperationError("消息去重表写入权限不足，操作未执行。请管理员在 Supabase SQL Editor 运行 migrations/005_bot_updates.sql 检查授权和 RLS 策略。")
    raise OperationError("消息去重记录失败，操作未执行，请联系管理员查看服务日志。")


def update_secret(values):
    target = required("SUPABASE_SECRET_ID")
    # id must be a primary key. Never perform a filterless PATCH.
    response = database("PATCH", "secret", params={"id": "eq." + target, "select": "id"}, json=values)
    if response.status_code != 200:
        raise OperationError("Supabase 更新失败，请检查表结构、权限和目标记录。")
    try:
        rows = response.json()
        if not isinstance(rows, list) or len(rows) != 1:
            raise OperationError("没有找到唯一目标记录，请检查 SUPABASE_SECRET_ID。")
    except ValueError:
        raise OperationError("Supabase 返回格式异常。") from None
