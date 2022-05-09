#!/bin/bash

poetry update
poetry install

if [ "x${NO_FORMAT}" == x ]; then
	ARGS="--format"
fi

poetry run python tools/generate-from-pymavlink.py ${ARGS}
