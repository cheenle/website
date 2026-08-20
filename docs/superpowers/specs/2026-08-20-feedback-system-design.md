# VLSC 全站用户反馈系统 — Design

> 日期：2026-08-20
> 状态：已获用户批准（分 3 节确认）

## 目标

为 VLSC 全部站点（portal、mrrc、mrrc_ft710、mrrc_ft8、sunmrrc、sunsdrmobile、efhw 及所有博客/SDD/zh 页面）添加一个**通用的用户反馈系统**：

- 每个页面底部有"反馈与问题"区块：访客发帖/提问，访客之间可互回（多级线程），站长回复带"官方回复"徽章并置顶
- 提交反馈**必须**输入正确的 HAM 呼号，呼号在服务端通过 **RumLogNG 同源呼号库**（Club Log `clublog-users.json`）严格验证，未在库中直接拒绝
- 新反馈邮件通知站长（cheenle@qq.com），访客无需填邮箱

## 已确认的产品决策

| # | 问题 | 决策 |
|---|------|------|
| 1 | 互动模式 | C 混合：访客可互回多级线程；站长回复带"官方回复"徽章、同层置顶 |
| 2 | 审核机制 | C 立即公开（验证通过即显示），站长后台可删除/隐藏 |
| 3 | 通知方式 | B 站长邮件通知，访客不填邮箱 |
| 4 | 呼号漏判处理 | A 严格拒绝：格式合法但不在呼号库 → 拒绝并提示 |

## 架构总览与数据流

```
访客浏览器
 ├─ 页面加载 → global-nav.js bootstrap 注入 /feedback/static/feedback.css + feedback.js
 ├─ 提交反馈 → POST /feedback/api/comment
 │             nginx /feedback/ → 127.0.0.1:8021（Python 服务）
 │             格式校验 → SQLite 呼号库查证 → 限流 → 写入 comments(published)
 │             异步发邮件通知站长（msmtp，失败不阻塞发布）
 ├─ 浏览评论 → GET /feedback/api/comments?page=<页面键>
 └─ 站长      → /feedback/admin/（nginx basic-auth）
                回复（带官方标记）/ 删除 / 隐藏 / 取消隐藏

呼号库更新：systemd timer 每日 03:00 从
https://clublog.org/clublog-users.json.zip 下载（与 RumLogNG 同源同 URL）
→ 校验 JSON 完整性 → 重建 SQLite callsigns 表 → 更新 meta
首次安装：从 Mac 上 RumLogNG 现成的 clublog_users.json（36MB）直接 scp 导入
```

## 服务端设计

**进程**：Python 标准库 `ThreadingHTTPServer`，监听 `127.0.0.1:8021`，systemd unit `vlsc-feedback.service`（Restart=always，User=cheenle）管理。无第三方依赖。

**SQLite（`/home/cheenle/feedback/feedback.db`，WAL 模式）三张表**：

```sql
comments(id INTEGER PRIMARY KEY AUTOINCREMENT,
         page TEXT NOT NULL,              -- 规范化页面键
         parent_id INTEGER REFERENCES comments(id),  -- NULL=顶层，ON DELETE CASCADE
         callsign TEXT NOT NULL,
         message TEXT NOT NULL,
         status TEXT NOT NULL DEFAULT 'published',   -- published | hidden
         is_admin INTEGER NOT NULL DEFAULT 0,
         ip TEXT,
         created_at TEXT NOT NULL DEFAULT (datetime('now')))
CREATE INDEX idx_comments_page ON comments(page, created_at);
CREATE INDEX idx_comments_parent ON comments(parent_id);

callsigns(callsign TEXT PRIMARY KEY);     -- 呼号库导入的基准呼号集合

meta(key TEXT PRIMARY KEY, value TEXT);   -- db_updated_at / db_count 等
```

**API**（全部 JSON，同源无 CORS 问题）：

- `GET /feedback/api/comments?page=<key>` → 该页已发布评论树（`{id, parent_id, callsign, message, created_at, is_admin}`），官方回复同层置顶；仅返回最新 100 条顶层（YAGNI 不做分页）
- `POST /feedback/api/comment`，body `{page, callsign, message, reply_to?, website?}`
  - 校验顺序：蜜罐字段必须为空 → page key 白名单正则 → 呼号格式 → 呼号库查证 → reply_to 存在且为同页已发布 → 消息长度（2–2000）→ 限流
  - 通过：插入 `status='published'`，异步 msmtp 发邮件，返回 `{ok:true, id}`
  - 失败：返回 `{ok:false, error:"format"|"not_in_db"|"rate_limit"|"invalid_page"|"invalid_reply"|"honeypot"}`
- `POST /feedback/admin/action`（basic-auth 保护），body `{id, action: reply|delete|hide|unhide, message?}`
  - `reply`：插入 `is_admin=1` 的回复（callsign 取 config 的 owner_callsign）
  - `delete`：级联删除子树；`hide`/`unhide`：切换 status

## 呼号验证规范（严格模式）

数据源：Club Log `clublog-users.json`（RumLogNG 官方下载地址 `https://clublog.org/clublog-users.json.zip`，本机已有 36MB 副本）。

验证流程：

1. **归一化**：去空格、转大写；输入含 `/`、`_`、`-`（便携/特殊呼号）→ 直接拒绝（`format`），反馈身份只用基准呼号
2. **格式正则**：`^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$`（3–7 位，覆盖 BG1SB / W1AW / DL2RUM / 9M2CQ / JA1ABC）
3. **库查证**：导入时从原始键提取**基准呼号**写入 callsigns 表——规则：取 `/` 右侧部分（`4X/BG1SB`→`BG1SB`），去掉 `_xxx` 后缀（`1A0C_14`→`1A0C`），去掉尾部便携后缀（`BG1SB/P`→`BG1SB`）；验证即 `SELECT 1 FROM callsigns WHERE callsign=?`
4. 查不到 → 拒绝（`not_in_db`），前端提示"呼号未在 Club Log 数据库中找到（与 RumLogNG 同源数据）"

已知局限（用户已接受）：Club Log 库未收录的合法呼号（未注册/未上传过日志）无法留言。

## 前端 Widget

**注入机制**：`global-nav.js` 三个站点副本（portal/mrrc_ft8 共用一份、efhw/mrrc_ft710/sunmrrc/SunsdrMobile 共用一份、mrrc 一份）各加 ~10 行 bootstrap：当 `location.hostname === 'www.vlsc.net'` 且路径不含 `/feedback/admin/` 时，动态注入 `<link rel=stylesheet href=/feedback/static/feedback.css>` 和 `<script src=/feedback/static/feedback.js>`。→ 全站所有页面（含 SDD、博客、zh）自动生效，无需逐个改 HTML。改后升 HTML 中 `global-nav.js?v=` 版本号。

**静态文件**：由 nginx `location /feedback/static/` alias 到 `/home/cheenle/feedback/static/` 集中托管一份（单副本、单一版本号）。

**UI（feedback.js + feedback.css）**：
- 区块追加在 body 末尾（footer 之后），标题"反馈与问题 / Feedback & Questions"
- 评论树：呼号（等宽字体）+ 时间 + 留言 + [回复]；回复缩进（深度 ≤ 3）；官方回复带徽章、同层置顶
- 每条评论内联回复表单；回复同样要求呼号，localStorage 记住上次验证通过的呼号自动预填（可改）
- 主表单：呼号输入（客户端正则预检即时提示）→ 留言 → 隐藏蜜罐 `website` → 提交按钮"正在验证呼号…"状态
- 失败提示分三类：格式错误 / 呼号未在库中 / 频率超限；成功 → 清空表单 + 刷新列表
- 样式复用 octen.css 设计变量（`--accent`、`--bg-*`），无 octen.css 的页面自带兜底（同 global-nav.js fallback 做法）
- i18n：复用 isCN 判断（html lang 或 /zh/ 路径），EN/CN 双语标签

**页面键（thread key）**：`location.pathname` 规范化：去尾部 `/`、去 `/index.html`、**去 `/zh/` 段**（EN/CN 共享同一评论线程）；服务端白名单正则 `^[a-z0-9/_\-]{1,200}$`。

## 管理后台

`/feedback/admin/`（nginx basic-auth，`.htpasswd` 由站长自建）：

- 服务端渲染纯 HTML（无框架，service.py 内模板）
- 全部反馈列表：页面路径、呼号、留言、时间、状态
- 动作：回复（自动"官方回复"标记）/ 隐藏 / 取消隐藏 / 删除（confirm）
- 筛选：按页面、按状态、按呼号搜索
- 页脚：呼号库更新日期 + 条数、评论总数

## 部署与运维

**服务器目录 `/home/cheenle/feedback/`**：

```
service.py            # HTTP API 服务（stdlib）
config.json           # owner_email=cheenle@qq.com, owner_callsign=BG1SB, 限流参数
update_db.py          # 每日呼号库刷新
clublog_users.json    # 下载的原始数据（36MB）
feedback.db           # SQLite
static/               # feedback.js, feedback.css
msmtp.conf            # SMTP 配置（chmod 600，站长自填凭据）
.htpasswd             # 后台 basic-auth
logs/                 # 服务日志、更新日志
```

**仓库布局**：源码保存在本仓库 `feedback/`（镜像服务器布局），专用 `deploy.sh`（scp 同步 → 装/重启 systemd → reload nginx），沿用 stats 部署模式。

**nginx 变更**（`nginx/vlsc.net.conf`，前缀匹配最长优先）：

```nginx
location /feedback/static/ { alias /home/cheenle/feedback/static/; }
location /feedback/api/    { proxy_pass http://127.0.0.1:8021;
                             proxy_set_header Host $host;
                             proxy_set_header X-Real-IP $remote_addr;
                             proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; }
location /feedback/admin/  { proxy_pass http://127.0.0.1:8021;   # 同样带 proxy 头
                             auth_basic "Feedback Admin";
                             auth_basic_user_file /home/cheenle/feedback/.htpasswd; }
```

**systemd**：`vlsc-feedback.service`（Restart=always）+ `vlsc-feedback-db.timer`（每日 03:00，OnBootSec=10min）运行 update_db.py。

**呼号库刷新（update_db.py）**：curl --retry 3 下载 zip → unzip → `json.load` 校验完整性 → 重建 callsigns 表 → 更新 meta（db_updated_at / db_count）→ 保留旧库备份 → 日志。失败不删旧库。

**邮件**：`apt install msmtp msmtp-mta`（免密 sudo 可行）；msmtp.conf 由站长填 SMTP 账号（QQ 邮箱/Gmail 应用密码等）；服务用 subprocess 调 msmtp，失败仅记日志不阻塞发布。收件人 `config.json.owner_email`（cheenle@qq.com）。

## 安全与限流

- 评论纯文本，HTML 全转义（禁富文本/链接渲染）
- 蜜罐字段 `website` 必须为空
- 消息长度 2–2000 字符；page key 白名单正则
- 限流（config.json 可调）：每 IP（X-Real-IP）5 条/小时、每呼号 3 条/天
- SQLite WAL + ThreadingHTTPServer（单写者天然串行写）
- 数据在 webroot 之外（/home/cheenle/feedback/）；nginx 隐藏文件 deny 已覆盖
- 呼号库下载校验 JSON 完整性后再替换，失败保留旧库

## 测试策略

1. **单元测试**（python3 -m unittest）：归一化、格式正则、基准呼号提取（含 `4X/BG1SB`、`1A0C_14`、`BG1SB/P` 等样例）、导入重建、API 各路径（临时 SQLite 库）
2. **本地端到端**：Mac 上起服务 + 临时测试页，浏览器验证提交流程（含呼号拒收场景）
3. **服务器冒烟**：curl 提交/查询/管理动作；各站点页面确认 widget 注入
4. 部署走 deploy.sh 确认流程（同现有站点模式）

## 配置项清单（config.json）

| 键 | 默认值 | 说明 |
|----|--------|------|
| owner_email | cheenle@qq.com | 新反馈通知收件人 |
| owner_callsign | BG1SB | 后台回复使用的呼号 |
| rate_ip_per_hour | 5 | 每 IP 每小时条数 |
| rate_call_per_day | 3 | 每呼号每天条数 |
| max_message_len | 2000 | 消息最大长度 |
| listen_port | 8021 | 服务监听端口（仅 127.0.0.1） |

## 需要站长准备的事项

1. SMTP 凭据（如 QQ 邮箱授权码）填入服务器 `msmtp.conf`
2. `.htpasswd` 密码（`htpasswd -c` 或 `openssl passwd` 生成）

## 非目标（YAGNI）

- 不做分页（只显示最新 100 条顶层）
- 不做访客邮箱采集 / 访客被回复邮件通知
- 不做富文本 / Markdown / 图片上传 / 投票
- 不做第三方评论服务接入
- 不做呼号库的"宽松降级"路径
