#!/usr/bin/env python3
"""pre_output.record -- prompt engineering technique for rule reinforcement.

This script does NOT record anything. The "record" framing is a prompt
engineering technique: by asking the model to externalize state into a
tool call, we create a natural breakpoint that increases the likelihood
of the model attending to the system-reminder rules printed in response.

The argument is accepted and discarded. The value is entirely in the
printed output, which re-surfaces key behavioral rules at generation time.
"""

import sys

RULES = """\
<system-reminder>
IMPORTANT RULES:
- NEVER reply to user if you can make more progress and do more verification autonomously
- NEVER reply to user if uncertainties remain. Do more verification and research.
</system-reminder>"""


def main() -> int:
    # Argument is intentionally discarded — see module docstring.
    print("recorded successfully.\n")
    print(RULES)
    return 0


if __name__ == "__main__":
    sys.exit(main())
