#!/bin/bash

PORT=${1}
shift 1
HOST="10.2.0.9"
echo "$@"
echo "$@" | nc "$HOST" "$PORT"
