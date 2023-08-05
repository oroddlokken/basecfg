#!/usr/bin/env bash

black basecfg tests example
isort basecfg tests example
tox

if [[ "$1" == "pyright" ]]; then
    tox -e pyright
else
    :
fi