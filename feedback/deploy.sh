#!/bin/bash
# VLSC 反馈系统部署脚本
# 用法: ./deploy.sh                # 同步代码 + 安装 systemd + 部署 nginx
#       ./deploy.sh --files-only   # 只同步代码
set -euo pipefail

REMOTE_HOST="www.vlsc.net"
REMOTE_USER="cheenle"
REMOTE_DIR="/home/cheenle/feedback"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══ VLSC 反馈系统部署 → $REMOTE_HOST ═══"

# ── 1. 本地校验 ──
for f in service.py callsign.py db.py update_db.py config.json \
         static/feedback.js static/feedback.css; do
  [ -f "$LOCAL_DIR/$f" ] || { echo "缺少文件: $f"; exit 1; }
done
python3 -m py_compile "$LOCAL_DIR"/service.py "$LOCAL_DIR"/callsign.py \
  "$LOCAL_DIR"/db.py "$LOCAL_DIR"/update_db.py
echo "✔ 本地校验通过"

# ── 2. 远端目录 ──
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR/static $REMOTE_DIR/logs"

# ── 3. 同步代码 ──
for f in service.py callsign.py db.py update_db.py config.json; do
  scp -q "$LOCAL_DIR/$f" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/"
done
scp -q "$LOCAL_DIR/static/feedback.js" "$LOCAL_DIR/static/feedback.css" \
  "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/static/"

# ── 4. systemd + nginx ──
if [[ "${1:-}" == "--files-only" ]]; then
  echo "（--files-only）跳过 systemd/nginx"
  exit 0
fi
read -r -p "安装/重启 systemd 并部署 nginx 配置？[y/N] " ans
if [[ "$ans" =~ ^[Yy]$ ]]; then
  scp -q "$LOCAL_DIR/vlsc-feedback.service" "$LOCAL_DIR/vlsc-feedback-db.service" \
      "$LOCAL_DIR/vlsc-feedback-db.timer" "$REMOTE_USER@$REMOTE_HOST:/tmp/"
  ssh "$REMOTE_USER@$REMOTE_HOST" "sudo install -m 644 /tmp/vlsc-feedback.service /etc/systemd/system/ && \
    sudo install -m 644 /tmp/vlsc-feedback-db.service /etc/systemd/system/ && \
    sudo install -m 644 /tmp/vlsc-feedback-db.timer /etc/systemd/system/ && \
    sudo systemctl daemon-reload && \
    sudo systemctl enable --now vlsc-feedback vlsc-feedback-db.timer && \
    sudo systemctl restart vlsc-feedback && \
    sleep 1 && sudo systemctl is-active vlsc-feedback"
  scp -q "$LOCAL_DIR/../nginx/vlsc.net.conf" "$REMOTE_USER@$REMOTE_HOST:/tmp/vlsc.net.conf"
  ssh "$REMOTE_USER@$REMOTE_HOST" "sudo cp /tmp/vlsc.net.conf /etc/nginx/sites-available/vlsc.net && \
    sudo nginx -t && sudo systemctl reload nginx && echo 'nginx OK'"
else
  echo "跳过 systemd/nginx（代码已同步）"
fi

echo
echo "✔ 部署完成。首次安装还需（详见 README.md）："
echo "  1) sudo apt install msmtp msmtp-mta"
echo "  2) 配置 $REMOTE_DIR/msmtp.conf（SMTP 凭据，chmod 600）"
echo "  3) 生成 $REMOTE_DIR/.htpasswd（后台密码）"
echo "  4) 导入呼号库: scp clublog_users.json $REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/ && \\"
echo "     ssh $REMOTE_USER@$REMOTE_HOST 'python3 $REMOTE_DIR/update_db.py --file $REMOTE_DIR/clublog_users.json'"
