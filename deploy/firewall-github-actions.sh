#!/bin/bash
# Разрешить SSH (порт 22) с IP GitHub Actions.
# Запускать на сервере: sudo ./deploy/firewall-github-actions.sh
set -e
[ "$(id -u)" -ne 0 ] && { echo "Run as root: sudo $0"; exit 1; }
echo "Fetching GitHub Actions IP ranges..."
if command -v jq &>/dev/null; then
  for cidr in $(curl -sf https://api.github.com/meta | jq -r '.actions[] | select(test("^[0-9]"))'); do
    ufw allow from "$cidr" to any port 22 comment "GitHub Actions" 2>/dev/null || true
  done
else
  echo "Install jq: apt install -y jq"
  exit 1
fi
ufw reload
echo "Done. Try deploy again."
