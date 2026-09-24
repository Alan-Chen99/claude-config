#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
node --check bin/spool
bin/spool --file /dev/null >/dev/null
echo "precommit ok"
