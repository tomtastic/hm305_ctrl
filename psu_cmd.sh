#!/bin/bash

PORT=${1}
shift 1
HOST="10.2.0.9"
#echo "$@"
X=$(echo "$@" | nc "$HOST" "$PORT")
echo "$X "
