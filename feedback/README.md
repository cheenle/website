# VLSC 反馈系统

全站用户反馈：访客用 HAM 呼号（Club Log 库严格验证，与 RumLogNG 同源）发帖/互回；
站长邮件通知 + 后台管理。

## 架构
- `service.py` — Python 标准库 HTTP 服务（127.0.0.1:8021，systemd 管理）
- `feedback.db` — SQLite：评论 + callsigns 呼号库 + meta
- `update_db.py` — 每日 03:00（systemd timer）从 clublog.org 刷新呼号库
- nginx：`/feedback/api/`（反代）、`/feedback/static/`（widget 静态）、
  `/feedback/admin/`（basic-auth 后台）
- 前端：global-nav.js 全站自动注入，widget 文件集中托管于 /feedback/static/

## 首次部署（服务器 www.vlsc.net）
1. `sudo apt install msmtp msmtp-mta`
2. 编辑 `/home/cheenle/feedback/msmtp.conf`（从 msmtp.conf.example 复制），
   填入 SMTP 凭据（QQ 邮箱授权码等），`chmod 600`
3. 生成后台密码：`htpasswd -c /home/cheenle/feedback/.htpasswd cheenle`
4. 导入呼号库（种子）：
   `scp clublog_users.json cheenle@www.vlsc.net:/home/cheenle/feedback/`
   `ssh cheenle@www.vlsc.net 'python3 /home/cheenle/feedback/update_db.py --file /home/cheenle/feedback/clublog_users.json'`
5. 验证：`curl -s https://www.vlsc.net/feedback/api/comments?page=/` → `{"ok":true,"comments":[]}`
   任一站点页面底部出现"反馈与问题"区块

## 日常运维
- 后台：https://www.vlsc.net/feedback/admin/（basic-auth）
- 呼号库日志：`/home/cheenle/feedback/logs/update.log`
- 服务日志：`journalctl -u vlsc-feedback -f`
- 重新部署：`cd feedback && ./deploy.sh`
- 手动刷新呼号库：`ssh cheenle@www.vlsc.net 'python3 /home/cheenle/feedback/update_db.py'`

## 呼号验证规则
- 格式正则 `^[0-9]?[A-Z]{1,2}[0-9][A-Z]{1,3}$`；拒绝便携/特殊形式（含 / _ -）
- 必须存在于 callsigns 表（从 clublog_users.json 提取基准呼号）
- 未收录的合法呼号无法留言（已知局限，产品决策 A）

## 配置（config.json）
owner_email / mail_from / owner_callsign / rate_ip_per_hour / rate_call_per_day /
max_message_len / listen_host / listen_port
