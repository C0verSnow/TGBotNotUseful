from pathlib import Path
from bot.config import OperationError

PATH = Path(__file__).resolve().parent.parent / "idlist.md"


def allowed(user_id):
    try:
        ids = {int(line.strip()) for line in PATH.read_text(encoding="utf-8").splitlines()
               if line.strip().isascii() and line.strip().isdigit()}
    except (OSError, ValueError):
        raise OperationError("白名单读取失败，请联系管理员。") from None
    return user_id in ids
