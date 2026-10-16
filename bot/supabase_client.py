import base64
import json

from bot.config import required, OperationError
from bot.http import request


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
    response = database("POST", "bot_updates", representation=False, json={"update_id": update_id})
    if response.status_code == 409:
        return False
    if response.status_code != 201:
        raise OperationError("消息去重记录失败，操作未执行，请联系管理员。")
    return True


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
