# 补齐统一部署脚本 — Design

> 日期：2026-08-12
> 状态：已获用户批准

## 目标

工作区根目录 `/Users/cheenle/HAM/website/deploy.sh` 已存在 VLSC Unified Deploy 脚本，覆盖 6 个站点。本次补齐缺口：新增 efhw 站点，并修正过时的站点数文本。

## 改动（全部在 deploy.sh）

1. **SITES 表新增 efhw**（加在 `sunsdmobile` 行之后）：
   ```
   "efhw|/Users/cheenle/HAM/website/efhw|efhw|https://$REMOTE_HOST/efhw/"
   ```
   - efhw 已满足预检（`index.html` + `css/octen.css` + `js/global-nav.js`）
   - 远程部署到 `/var/www/vlsc.net/efhw`，与 nginx alias 一致
   - 自动继承：备份 `/var/www/backups/efhw_<ts>`、提取+权限、单次 nginx reload

2. **第 6 行** `# ./deploy.sh  # deploy all 4 sites (prompt to confirm)` → `deploy all 7 sites`

## 验证

- 运行 `./deploy.sh --list` 应列出全部 7 站（portal/mrrc/mrrc_ft710/mrrc_ft8/sunmrrc/sunsdrmobile/efhw）
- `./deploy.sh --yes efhw` 冒烟测试部署 efhw（可选，需 SSH）
- `bash -n deploy.sh` 语法检查通过
