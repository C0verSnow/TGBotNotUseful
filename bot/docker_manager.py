import os
import re
from urllib.parse import quote
from bot.config import required, OperationError
from bot.http import request


def dispatch(action, chat_id, update_id):
    if action not in {"start", "stop"}:
        raise OperationError("Docker 只允许 start 或 stop。")
    owner, repo = required("GITHUB_OWNER"), required("GITHUB_REPO")
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]+", part) for part in (owner, repo)):
        raise OperationError("GitHub 仓库配置错误。")
    workflow = quote(os.environ.get("GITHUB_WORKFLOW", "docker-control.yml"), safe="")
    response = request("POST", f"https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow}/dispatches",
                       headers={"Authorization": "Bearer " + required("GITHUB_TOKEN"),
                                "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"},
                       json={"ref": required("GITHUB_REF"), "inputs": {"action": action,
                             "chat_id": str(chat_id), "request_id": str(update_id)}})
    if response.status_code != 204:
        raise OperationError("GitHub 工作流提交失败，请检查令牌权限、分支和工作流。")
