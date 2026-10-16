import httpx
from bot.config import OperationError


def request(method, url, **kwargs):
    try:
        with httpx.Client(timeout=httpx.Timeout(8, connect=3), follow_redirects=False) as client:
            return client.request(method, url, **kwargs)
    except httpx.HTTPError:
        raise OperationError("外部服务连接失败或超时，请检查服务状态。") from None
