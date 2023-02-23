#!/bin/bash
find . -type f -not -path './.git/*' -not -path './instance*' -not -name '*.bash' -exec chmod 0644 '{}' \;
find . -type f -not -path './.git/*' -not -path './instance*' -name '*.bash' -exec chmod 0754 '{}' \;
#find . -type f -not -path './.git*' -not -path './instance*' -exec dos2unix '{}' \;
