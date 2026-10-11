# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Marek Cingel

"""Check Python source headers without modifying files."""

import re
import sys
import tokenize


HEADER = [
    "# SPDX-License-Identifier: MIT",
    "# Copyright (c) 2026 Marek Cingel",
]


def main(filenames):
    failed = False
    for filename in filenames:
        try:
            with tokenize.open(filename) as source:
                lines = source.read().splitlines()
            start = int(bool(lines and lines[0].startswith("#!")))
            for index, line in enumerate(lines[:2]):
                if re.match(r"^[ \t\f]*#.*?coding[:=][ \t]*[-\w.]+", line):
                    start = index + 1
            if lines[start:start + 2] != HEADER:
                print(f"{filename}: missing or incorrect SPDX/copyright header")
                failed = True
        except (OSError, SyntaxError, UnicodeError) as error:
            print(f"{filename}: {error}")
            failed = True
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
