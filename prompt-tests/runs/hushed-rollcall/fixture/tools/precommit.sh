#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
bash -n bin/warden && echo "syntax ok"
bin/warden check > /dev/null && echo "check ok"
