# Generated from partner-sdk 3.2.1 by tools/vendor.sh.
# Do not edit: this directory is overwritten on the next vendor run and local
# changes are lost without a diff.

import datetime

_FORMAT = "%Y-%m-%d"


def parse_date(text):
    """The date in `text`, or None when it is not a date in the partner format."""
    try:
        return datetime.datetime.strptime(text, _FORMAT).date()
    except (TypeError, ValueError):
        return None
