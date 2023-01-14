#!/bin/bash
find . -type f -exec dos2unix '{}' \;
find . -type f -exec chmod 0644 '{}' \;
find . -type d -exec chmod 0755 '{}' \;
