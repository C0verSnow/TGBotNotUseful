"""Send a fixed final result without exposing shell output or credentials."""
import os
import re
import sys
import time
import httpx


def main():
    action, chat, request_id = (os.environ[name] for name in ("ACTION", "CHAT_ID", "REQUEST_ID"))
    if action not in {"start", "stop"} or not re.fullmatch(r"[0-9]+", chat) or not re.fullmatch(r"[0-9]+", request_id):
        sys.exit("Invalid notification input")
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        sys.exit("Missing Actions secret: TELEGRAM_BOT_TOKEN. Vercel variables are not shared with GitHub Actions.")
    result = os.environ["RESULT"]
    if result == "success":
        text = f"✅ Docker {'启动' if action == 'start' else '停止'}成功"
    else:
        text = f"❌ Docker 操作未确认成功（{result}），请检查 Actions 中的连接和执行步骤。"
    text += f"\n服务器：{os.environ.get('DEPLOY_HOST') or '未配置 DEPLOY_HOST'}\n操作：{action}\n任务编号：{request_id}"
    text += f"\n工作流：https://github.com/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    for attempt in range(3):
        try:
            response = httpx.post(url, json={"chat_id": chat, "text": text}, timeout=10)
            if response.status_code == 200 and response.json().get("ok") is True:
                return
            # Telegram descriptions and exception text can contain sensitive data.
            print(f"Telegram notification rejected: HTTP {response.status_code}", file=sys.stderr)
            if response.status_code in {400, 401, 403, 404}:
                sys.exit("Check Actions TELEGRAM_BOT_TOKEN and whether the recipient can receive bot messages.")
        except (httpx.HTTPError, ValueError):
            print("Telegram notification transport or response error", file=sys.stderr)
        time.sleep(attempt + 1)
    sys.exit("Final Telegram notification failed; inspect configuration (no credentials logged)")


if __name__ == "__main__":
    main()
