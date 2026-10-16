from bot.config import required, OperationError
from bot.http import request


def call(method, payload):
    response = request("POST", f"https://api.telegram.org/bot{required('TELEGRAM_BOT_TOKEN')}/{method}", json=payload)
    if response.status_code != 200:
        raise OperationError("Telegram 消息发送失败。")
    try:
        if response.json().get("ok") is not True:
            raise OperationError("Telegram 消息发送失败。")
    except ValueError:
        raise OperationError("Telegram 返回格式异常。") from None


def send(chat_id, text):
    call("sendMessage", {"chat_id": chat_id, "text": text})


def delete(chat_id, message_id):
    try:
        call("deleteMessage", {"chat_id": chat_id, "message_id": message_id})
        return True
    except OperationError:
        return False
