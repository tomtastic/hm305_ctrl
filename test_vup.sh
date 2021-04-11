#!/bin/bash


echo "INIT 0" | nc 127.0.0.1 $1

#for i in {0..300}; do
#  v=$(bc <<< "scale=1; $i/10")
#  echo "VOLT:UP $v"
#  echo "VOLT:UP $v" | nc 127.0.0.1 $1
#done


for i in {0..300}; do
  V="$(bc <<< "scale=2; 0.1+$(echo 'VOLT:SETP? ' | nc 127.0.0.1 $1)")"
  echo VOLT $V
  echo VOLT $V | nc 127.0.0.1 $1
done