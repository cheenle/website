# VLSC Projects — website workspace

Source for **[www.vlsc.net](https://www.vlsc.net/)**: the unified landing page, the blog,
the nginx server block, the feedback service, and the engineering record behind the VLSC
open-source remote-radio ecosystem.

Everything here is **pure static HTML/CSS/JS plus a little Python**. No framework, no
bundler, no `npm install`, no build step. You edit files and deploy them.

## What is in this repository

| Path | What it is |
|---|---|
| `portal/` | The DocumentRoot site — landing page, `/agentic.html` (thesis), `/engineering.html` (mechanism), `blog/`, `zh/` mirrors, `deploy.sh` |
| `efhw/` | The EFHW Fuchs ATU V3.0 product site and antenna knowledge pages |
| `nginx/vlsc.net.conf` | Reference copy of the server block deployed at `/etc/nginx/sites-enabled/vlsc.net` |
| `feedback/` | Feedback intake service on the Python standard library only — `http.server.ThreadingHTTPServer`, no web framework and no third-party dependencies: `service.py`, `db.py` (SQLite), `callsign.py`, systemd units, tests |
| `manage/` | Terraform for the host (`main.tf`, `variables.tf`, `terraform.tfvars.example`) |
| `stats/` | `analyze_nginx.py` — nginx access log → SQLite → HTML dashboard |
| `docs/superpowers/` | 12 design specs and 10 implementation plans. This is the working record of how changes were decided, not decoration |
| `CLAUDE.md` | Instructions for AI agents working in this repo. Humans: it is also the clearest description of the deploy and editorial rules |

## The sub-sites live in other repositories

`mrrc/`, `mrrc_ft710/`, `mrrc_modern/`, `mrrc_ft8/`, `ft8/`, `sunmrrc/` and
`SunsdrMobile/` are **symlinks**, tracked by git as symlinks. They point at paths on the
maintainer's machine and resolve to separate repositories:

| Symlink | Repository | Live at |
|---|---|---|
| `mrrc/` | [`cheenle/UHRR_mac`](https://github.com/cheenle/UHRR_mac) | [/mrrc/](https://www.vlsc.net/mrrc/) |
| `mrrc_ft710/` | [`cheenle/mrrc_ft710`](https://github.com/cheenle/mrrc_ft710) | [/mrrc_ft710/](https://www.vlsc.net/mrrc_ft710/) |
| `mrrc_modern/` | [`cheenle/mrrc_modern`](https://github.com/cheenle/mrrc_modern) | [/mrrc_modern/](https://www.vlsc.net/mrrc_modern/) |
| `mrrc_ft8/`, `ft8/` | [`cheenle/mrrc_ft8`](https://github.com/cheenle/mrrc_ft8) | [/mrrc_ft8/](https://www.vlsc.net/mrrc_ft8/) |
| `sunmrrc/`, `SunsdrMobile/` | [`cheenle/sunsdr`](https://github.com/cheenle/sunsdr), [`cheenle/SunsdrMobile`](https://github.com/cheenle/SunsdrMobile) | [/sunmrrc/](https://www.vlsc.net/sunmrrc/), [/sunsdrmobile/](https://www.vlsc.net/sunsdrmobile/) |

**On a fresh clone these symlinks are dangling.** That is expected. Clone the sibling
repositories alongside this one and recreate the links, or just work inside `portal/` and
`efhw/`, which are real directories. Commits to a sub-site belong to the owning repository,
never to this one.

## Two asset directories are deliberately untracked

`portal/images/` and `efhw/images/` hold the WeChat group QR code, which expires and is
regenerated roughly weekly. Tracking it would mean a churn commit every week, so the files
live on disk only. The tracked HTML references them, which means **a fresh clone renders a
broken QR image** until you drop the file in place. Deployment is unaffected: `deploy.sh`
tars the working directory, not the git index.

## Tests

Contract tests live in `portal/tests/` — five files covering the agentic/engineering pages,
the sitemap, and the two long-form articles. They assert section structure, evidence-labelling
discipline, forbidden phrasings, and that published numbers still match the census.

```bash
cd portal
/usr/bin/python3 -m pytest tests -q
```

**Use `/usr/bin/python3`.** On the maintainer's machine that is the system Python 3.9 with
pytest installed; the Homebrew `python3`, `python3.11`, `python3.12` and `python3.13` have
no pytest module and there is no virtualenv. If your own environment differs, use whatever
interpreter has pytest — nothing here depends on 3.9 specifically.

`sitemap.xml` is generated, not hand-edited:

```bash
cd portal && python3 make_sitemap.py
```

## Deploying

Each site deploys itself; there is no CI.

```bash
cd portal && ./deploy.sh     # landing page, blog, agentic, engineering → DocumentRoot
cd efhw   && ./deploy.sh     # EFHW product site → /efhw/
```

The scripts validate required files, tar the site, back up the live copy over SSH, copy,
extract, set ownership, and reload nginx. They ask before touching the remote.

`/var/www/vlsc.net` is a **shared DocumentRoot**: the portal owns the loose files at its
root and each sub-site owns its own directory via an nginx `alias`. So no script may ever
`rm -rf`, `chown -R` or `chmod -R` the DocumentRoot as a whole, and a rollback hint may
only restore the one site it came from. `CLAUDE.md` records the four deploy rules and the
incidents that produced them — they are worth reading before you edit any `deploy.sh`.

Note that `deploy.sh`, `portal/tests/` and `portal/make_sitemap.py` are build-time tooling
and are excluded from the published package. The DocumentRoot is world-readable.

## Engineering method

This project is documented as an agentic-engineering case study, and the documentation is
held to the same standard as the code:

- **[Agentic Engineering](https://www.vlsc.net/agentic.html)** — the thesis, the division
  between delegated execution and retained human judgment, and the cross-project evidence
  ledger. The ledger at `/agentic.html#evidence` is the single source of truth for
  comparable numbers (versions, test counts, release status, known defects); sub-sites link
  to it rather than self-reporting.
- **[Engineering Mechanism](https://www.vlsc.net/engineering.html)** — harness, nested
  feedback loops, the living SDD, and the maturity ladder.
- **[Seven Billion Tokens, One Field Incident](https://www.vlsc.net/blog/seven-billion-tokens/)**
  / [《格物致知 —— Agentic AI 的思考》](https://www.vlsc.net/blog/seven-billion-tokens/zh/)
  — an end-to-end account from one business intent to delivery and self-correction, opening
  with a token census across nine agent harnesses and including the measurement the author
  got wrong by 1.6 billion tokens.

Two editorial rules are enforced by the contract tests and are easy to violate by accident:

- **Never claim a product family was built by AI or agents.** Process evidence is graded
  separately from product maturity and never promotes it.
- **A repository without `.agents/skills/sdd-guardian/` must not be described as having a
  pre-edit gate.** Only `mrrc_ft710`, `mrrc_modern` and `mrrc_ft8` have one.

## Site-wide searching

Read the "Cross-site checks" section of `CLAUDE.md` before grepping. Short version: use a
shell **array** of site directories, never a string variable, and never grep `.` from the
workspace root — both mistakes report a clean tree while silently missing every sub-site.

## Licensing

There is no repository-level `LICENSE`. The sub-projects carry their own: the radio control
projects are GPLv3, `SunsdrMobile` is MIT, and EFHW hardware is GPL-3.0 / CERN-OHL-S 2.0.
Page footers state the applicable licence per project.

## 中文

本仓库是 [www.vlsc.net](https://www.vlsc.net/) 的源码工作区：门户落地页、博客、nginx
配置、反馈服务，以及 VLSC 开源远程无线电生态的工程记录。全部是静态 HTML/CSS/JS 加少量
Python，没有框架、没有构建步骤。

七个子站目录是指向兄弟仓库的符号链接，新克隆时会是悬空链接，属预期行为。`portal/images/`
与 `efhw/images/` 刻意不入库（二维码每周重生成）。测试请用 `/usr/bin/python3 -m pytest
portal/tests`。方法论见 [智能体工程总纲](https://www.vlsc.net/zh/agentic.html)、
[工程机制卷](https://www.vlsc.net/zh/engineering.html) 与
[《格物致知 —— Agentic AI 的思考》](https://www.vlsc.net/blog/seven-billion-tokens/zh/)。
