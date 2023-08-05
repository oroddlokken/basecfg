#!/usr/bin/env bash

egrep --color=auto -Iirn --exclude-dir=htmlcov '(TODO|FIXME)' basecfg tests
cat TODO
