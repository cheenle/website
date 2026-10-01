# MRRC Cloud Hub 接入导航与门户 — 实施计划

规格：`docs/superpowers/specs/2026-10-01-mrrc-hub-integration-design.md`

## 任务

1. **软链改名**：`mv /Users/cheenle/HAM/website/website /Users/cheenle/HAM/website/mrrc_hub`
2. **共享导航 4 份 `global-nav.js`**（portal 先改，它是 hub 新副本的源）：
   - `PATHS.mrrc_hub: '/mrrc_hub/'`
   - SITE 检测 `else if (/\/mrrc_hub\//.test(p)) SITE = 'mrrc_hub';`
   - `siteLink('mrrc_hub', 'Hub') +` 放在 `siteLink('mrrc_modern', 'Modern') +` 之后
3. **共享导航 2 份 `scope.js`**（sunmrrc / mrrc_ft8）：同上三处
4. **hub 新副本**：`cp portal/js/global-nav.js hub/mrrc_hub/website/js/global-nav.js`
5. **hub 5 页**：body 加 `data-site="mrrc_hub"`；`</body>` 前加 `<script src="js/global-nav.js?v=1" defer></script>`（2 空格缩进风格）
6. **hub 仓配套**：`deploy.sh` REQUIRED_FILES + `website/README.md` + `SDD/14-version-history.md`
7. **portal 内容**：`index.html` / `zh/index.html` / `about.html` / `zh/about.html` / `contact.html` / `zh/contact.html` / `privacy.html` / `zh/privacy.html`
8. **portal 清单与测试**：`make_sitemap.py`（SUBSITES）→ 重生成 `sitemap.xml`；两个测试文件
9. **nginx 参考副本**：从 live 整份同步
10. **CLAUDE.md**：站点清单 / 软链列表 / SITES 数组
11. **验证**：`pytest portal/tests`；本地 `http.server` 目视；hub 仓闸门
12. **提交**：website 仓一份；hub 仓只提交本次触碰的文件
13. **发布**：`portal/deploy.sh --force`、`hub/.../website/deploy.sh --yes`，随后 curl 逐页核验

## 顺序理由

先改 portal 的 canonical 脚本 → hub 副本才有正确内容；先改共享脚本 → hub 页面接入后立即生效；portal 文案与清单可并行；nginx 与发布放最后。
