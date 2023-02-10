#!/bin/bash
find . -type f -not -path './.git*' -not -name '*.bash' -exec chmod 0644 '{}' \;
find . -type f -not -path './.git*' -name '*.bash' -exec chmod 0754 '{}' \;
find . -type f -not -path './.git*' -exec dos2unix '{}' \;
