#!/usr/bin/env bash
# Build the wheel, upload it, sign the upload. Run from the repository root.
set -euo pipefail

: "${LEDGER_SIGNING_KEY:?export LEDGER_SIGNING_KEY before running this}"

python -m build --wheel
twine upload dist/*.whl
WHEEL=$(ls dist/*.whl | tail -1)
sign --key "$LEDGER_SIGNING_KEY" "$WHEEL"
echo "uploaded: $WHEEL"
