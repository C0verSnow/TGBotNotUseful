import re
import shlex
from bot import telegram
from bot.config import OperationError
from bot.whitelist import allowed
from bot.supabase_client import claim, update_secret
from bot.docker_manager import dispatch

FORMAT = "❌ 命令格式错误\n\n正确格式：\n/update_secret API_KEY=xxx API_SECRET=yyy"


def parse_secret(arguments):
    try:
        tokens = shlex.split(arguments)
    except ValueError:
        raise OperationError(FORMAT) from None
    values = {}
    for token in tokens:
        key, separator, value = token.partition("=")
        if not separator or key not in {"API_KEY", "API_SECRET"} or key in values or not value:
            raise OperationError(FORMAT)
        values[key] = value
    if set(values) != {"API_KEY", "API_SECRET"}:
        raise OperationError(FORMAT)
    return values


def handle(update):
    message = update.get("message")
    if not isinstance(message, dict):
        return
    sender, chat = message.get("from", {}), message.get("chat", {})
    if not isinstance(sender, dict) or not isinstance(chat, dict):
        return
    text = message.get("text", "")
    user_id, chat_id = sender.get("id"), chat.get("id")
    if type(user_id) is not int or type(chat_id) is not int or not isinstance(text, str) or sender.get("is_bot"):
        return
    match = re.fullmatch(r"/(id|update_secret|docker)(?:@[A-Za-z0-9_]+)?(?:\s+(.*))?", text, re.DOTALL)
    if not match:
        return
    command, arguments = match.group(1), (match.group(2) or "").strip()
    if command == "id":
        telegram.send(chat_id, f"你的 Telegram User ID：{user_id}")
        return
    deleted = False
    if command == "update_secret" and type(message.get("message_id")) is int:
        deleted = telegram.delete(chat_id, message["message_id"])
    try:
        if not allowed(user_id):
            raise OperationError("❌ 权限不足\n\n你的 Telegram User ID 不在白名单中。")
        if chat.get("type") != "private":
            raise OperationError("管理命令请在与机器人的私聊中使用。")
        if command == "update_secret":
            values = parse_secret(arguments)
        elif arguments not in {"start", "stop"}:
            raise OperationError("❌ 命令格式错误\n/docker start\n/docker stop")
        update_id = update.get("update_id")
        if type(update_id) is not int or update_id < 0:
            raise OperationError("消息编号无效，操作未执行。")
        if not claim(update_id):
            return
        if command == "update_secret":
            update_secret(values)
            result = "✅ Supabase Secret 更新成功\n\nAPI_KEY：已更新\nAPI_SECRET：已更新"
        else:
            dispatch(arguments, chat_id, update_id)
            result = f"⏳ Docker {arguments} 任务已提交（编号 {update_id}）。\n这还不是执行成功；完成后会另发最终结果。"
    except OperationError as error:
        result = str(error)
    if command == "update_secret" and not deleted:
        result += "\n\n原命令未能删除，请手动删除聊天中的密钥。"
    telegram.send(chat_id, result)
