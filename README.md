# TGBot

Python Telegram 管理机器人，部署到 Vercel，通过 Webhook 接收命令。

- `/id`：所有人可查询自己的 Telegram User ID。
- `/update_secret API_KEY=xxx API_SECRET=yyy`：白名单用户在私聊更新 Supabase 的固定记录，并尽量删除原消息。
- `/docker start`、`/docker stop`：白名单用户通过 GitHub Actions → Tailscale → 验证主机身份的 SSH，启停预先配置的现有容器。

Supabase 使用 `SUPABASE_KEY` 公钥（publishable 或 legacy anon），不使用 service_role 私钥。按需求开放匿名写入：拿到项目 URL 和公钥的人可以绕过机器人修改密钥、写入去重编号；密钥列不开放读取。升级时需要重新执行 `schema.sql` 并重新部署。

完整部署步骤见 [使用文档](使用文档.md)。首次配置数据库运行 [schema.sql](schema.sql)，环境变量样例见 [.env.example](.env.example)。默认白名单为空。

Vercel 只提交 Docker 任务；Actions 的独立通知任务发送实际执行结果。所有请求设置超时，Telegram 更新编号通过 Supabase 唯一主键去重。SSH 脚本与容器操作脚本分开，参考 Orders3 的职责组织，但不拉镜像、不重建容器。

测试由 `.github/workflows/checks.yml` 在 GitHub 运行，不在本地编译或运行测试。过程记录见 [tasklist.md](tasklist.md)。
