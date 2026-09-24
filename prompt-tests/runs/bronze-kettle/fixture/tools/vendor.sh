#!/usr/bin/env bash
# Re-download the partner SDK and replace partnerlib/ with its dates module.
#
#   tools/vendor.sh <sdk-tarball>
#
# The directory is replaced wholesale. Anything edited in place is gone.
set -euo pipefail
TARBALL="${1:?usage: tools/vendor.sh <sdk-tarball>}"
WORK="$(mktemp -d)"
tar -xf "$TARBALL" -C "$WORK"
rm -rf partnerlib
cp -a "$WORK/partner_sdk/dates" partnerlib
echo "partnerlib/ replaced from $TARBALL"
