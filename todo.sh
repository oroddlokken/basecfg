#!/usr/bin/env bash

egrep --color=auto -Iirn --exclude-dir=htmlcov '(TODO|FIXME)' voecfg tests
cat TODO
