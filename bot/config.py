import os
from dotenv import load_dotenv

load_dotenv()


class OperationError(Exception):
    """Only a fixed, non-sensitive user message may leave the service layer."""


def required(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise OperationError("服务配置不完整，请联系管理员检查环境变量。")
    return value
