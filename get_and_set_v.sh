#!/bin/bash

PORT=${1}
INC=${3}
CMD=${2}
HOST="10.2.0.9"

SEND() {
  echo "$@" | nc "$HOST" "$PORT"
}

case "$CMD" in
"VA")
  V="$(bc <<< "scale=2; $(echo 'VOLT:SETP? ' | nc "$HOST" "$PORT")+$INC")"
  SEND "VOLT $V"
  ;;
"OUTPUT")
  case $(SEND 'OUT?') in
  "ON")
    SEND "OUTPUT OFF"
    ;;
  "OFF")
    SEND "OUTPUT ON"
    ;;
  esac
esac




