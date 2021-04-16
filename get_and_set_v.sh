#!/bin/bash

PORT=${1}
INC=${3}
CMD=${2}


SEND() {
  echo "$@" | nc 127.0.0.1 "$PORT"
}

case "$CMD" in
"VA")
  V="$(bc <<< "scale=2; $(echo 'VOLT:SETP? ' | nc 127.0.0.1 $PORT)+$INC")"
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




