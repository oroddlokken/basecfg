#!/usr/bin/env bash

black voecfg tests
isort voecfg tests
tox

if [[ "$1" == "pyright" ]]; then
pyright voecfg tests
fi