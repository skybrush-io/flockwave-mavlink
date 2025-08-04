#!/bin/bash

uv sync

if [ "x${NO_FORMAT}" == x ]; then
	ARGS="--format"
fi

uv run python tools/generate-from-pymavlink.py ${ARGS}
