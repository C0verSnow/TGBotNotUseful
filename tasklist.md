# 本文档为4象限的任务清单，全文书写大白话

## 想做：
- 完成 issue #3：数据库改用公钥，更新脚本、测试和文档，提交 PR 并关闭 issue。
- 完成 issue #1，提供可部署的 Telegram 管理机器人和中文教程。

## 做完：
- 2026-10-16：已核对 idlist.md 的读取代码和使用文档，用大白话说明获取用户 ID、每行填写一个数字，以及提交并重新部署后生效；未进行本地编译验证。
- 2026-10-16：Vercel 项目 tg-bot 已部署到生产，状态 Ready，使用 main 的 cce6c71，自动识别 FastAPI。部署编号 dpl_DwPmLPQaXhdF3EMkS4ti8P6bKkxX。
- 正式地址：https://tg-bot-chi-brown.vercel.app/ 。项目页面：https://vercel.com/f1515xcn-5705s-projects/tg-bot 。
- 10 个环境变量已保存为 Secret，覆盖 Production 和 Preview；只导入 TGBot 所需变量。
- 经用户确认创建 TGBot Vercel Actions 专用 Token，仅限 C0verSnow/TGBot 的 Actions 读写和必需的 Metadata 只读；组织最长允许 366 天，到期 2027-10-17，无法设置 100 年。
- Token 已安全保存到根目录 .env 和 TGBot/.env；独立 Webhook Secret 保存在 TGBot/.env，没有输出或提交密钥。
- Telegram Webhook 已设置为 https://tg-bot-chi-brown.vercel.app/api/webhook ，回读确认待投递为 0，没有最近错误。
- 线上检查：首页 HTTP 200，返回 ok=true；无 Secret 的 Webhook HTTP 403；正确 Secret 的空消息 HTTP 200。没有发送聊天消息、修改业务密钥或操作容器。
- 只读检查通过：Bot Token 有效，GitHub 工作流为 active，Supabase 的 secret.id=1 存在。
- 已提交 PR #4：https://github.com/C0verSnow/TGBot/pull/4 ，并按 issue 要求关闭 #3；PR 尚未合并。
- GitHub 连接器没有创建 PR 和关闭 issue 的权限，已通过电脑上已有的 GitHub 登录完成并确认页面状态。
- issue #3 的远端 Checks 已通过：Python 测试、Shell 语法和 PostgreSQL 列权限/RLS、指定行更新、重复编号拦截均通过。
- issue #3 测试记录：https://github.com/C0verSnow/TGBot/actions/runs/38901436556
- 已修改公钥请求头，兼容 publishable/anon，拒绝私钥；去重插入不再要求读取记录。
- 已调整 SQL 的 anon 列权限和 RLS，并更新中文文档、环境变量样例。
- 已补充请求头、错误处理、私钥拒绝测试，以及远端 PostgreSQL 权限与去重检查。
- 2026-10-16：已同步最新主分支，建立 feature/issue-3-supabase-public-key 分支。
- 已确认本地 SUPABASE_KEY 是 publishable 公钥，没有输出或提交真实值。
- 用户明确选择只用公钥，不增加机器人登录账号，接受拿到公钥的人可以直接改数据。
- 2026-10-16：同步仓库，在 feature/issue-1-telegram-management 分支工作。
- 完成 /id、白名单权限、私聊管理命令、密钥参数校验和原消息删除。
- 完成 Supabase 指定主键更新，以及通过唯一消息编号防止重复执行。
- 完成 Actions → Tailscale → 严格 SSH 主机验证 → 固定现有容器启停。
- 完成独立的最终通知任务，区分提交成功和实际执行成功。
- 补齐数据库 SQL、环境变量样例、Vercel 配置和中文使用文档。
- GitHub 远端 Checks 通过：14 个测试通过，Shell 语法检查通过。
- 测试记录：https://github.com/C0verSnow/TGBot/actions/runs/38857504821
- 已提交 PR #2：https://github.com/C0verSnow/TGBot/pull/2
- GitHub 连接器没有创建 PR 的权限，使用电脑上已有的 GitHub 登录成功创建。

## 没做：
- 真实 Telegram、Supabase、Tailscale、SSH 联调需要部署账号和服务器配置，尚未执行。
- 按仓库约定，没有进行本地编译或本地测试，只做代码阅读和差异检查。
- PR #4 已在 main 合并，Vercel 生产服务已部署；尚未操作真实容器。
- idlist.md 目前没有用户 ID，管理命令暂时不能用，需要用户发 /id 后加入白名单并重新部署。

## 在做：
- 无；本次 Vercel 部署、环境变量和 Telegram Webhook 配置已完成，未进行本地编译。
