#!/usr/bin/env bash

black voecfg tests example
isort voecfg tests example
tox

if [[ "$1" == "pyright" ]]; then
    tox -e pyright
else
    :
fi