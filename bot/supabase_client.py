from bot.config import required, OperationError
from bot.http import request


def database(method, table, **kwargs):
    key = required("SUPABASE_KEY")
    return request(method, required("SUPABASE_URL").rstrip("/") + "/rest/v1/" + table,
                   headers={"apikey": key, "Authorization": "Bearer " + key,
                            "Prefer": "return=representation"}, **kwargs)


def claim(update_id):
    # A unique primary key makes concurrent/retried deliveries fail closed.
    response = database("POST", "bot_updates", json={"update_id": update_id})
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
