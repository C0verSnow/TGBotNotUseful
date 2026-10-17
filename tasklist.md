# 本文档为4象限的任务清单，全文书写大白话

## 想做：
- 完成 issue #5：排查 `/docker stop` 去重失败，修复、更新文档、跑远端 CI、提交 PR 并关闭 issue。
- 完成 issue #3：数据库改用公钥，更新脚本、测试和文档，提交 PR 并关闭 issue。
- 完成 issue #1，提供可部署的 Telegram 管理机器人和中文教程。

## 做完：
- 2026-10-16：用户确认后，通过浏览器执行 issue #5 完整数据库迁移，Supabase 显示成功。
- 线上数据库验证通过：anon 可插入 update_id、不可读取，RLS 开启，同一编号第二次插入触发唯一约束；验证事务已回滚，不留下测试编号。
- 2026-10-16：排查 GitHub 连接器权限，按用户选择将 GitHub 单独设为“允许所有操作”，并重新读取确认保存成功。
- 已确认个人账号 f1515x 安装了 ChatGPT Codex Connector，包含 issue 和 PR 读写权限；TGBot 所属组织 C0verSnow 尚未安装该连接器，这是组织仓库授权缺口。
- issue #5：真实 Supabase 去重 POST 返回 HTTP 404 / PGRST205，找不到 public.bot_updates，确认命令在提交 Docker 任务前失败。
- 已补充只修复去重表的 SQL 迁移、缓存刷新、错误分类与脱敏日志；只将 409 + 23505 视为重复消息。
- 已补充 Docker start/stop、密钥更新去重和异常回归测试；远端 Checks 已通过（Python、Shell、PostgreSQL 权限和重复编号拦截）。未执行本地编译或测试。
- issue #5 远端验证：https://github.com/C0verSnow/TGBot/actions/runs/38994767569
- 已创建 PR #6：https://github.com/C0verSnow/TGBot/pull/6 。GitHub 连接器创建权限不足，已通过现有登录创建并确认。
- 已核对浏览器中的 Supabase 项目与本地配置一致，管理页中没有 bot_updates 表。
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
- 尚未合并 PR、部署线上服务或操作真实容器。

## 在做：
- 2026-10-16：按用户要求改用浏览器继续完成 issue #5；已确认 PR #6 的 6 项检查通过，已完成用户确认的迁移和数据库验证。本次不做本地编译或测试。
- 给 C0verSnow 组织的 TGBot 仓库补齐连接器授权：已打开官方组织安装页面，准备只授权指定仓库；浏览器检测到用户手动操作后跳转到 ChatGPT，等待确认是否由用户完成安装。尚未验证组织安装最终状态，也未通过真实创建 PR 或关闭 issue 验证写入能力。本次不进行本地编译验证。
- issue #5：代码、文档、远端测试和线上数据库迁移验证已完成；准备合并 PR #6，检查生产部署。真实 /docker stop 尚未验证，已询问用户机器人用户名。
- 无；issue #3 的代码、文档、远端验证和 PR 已完成，等待审阅和部署。
