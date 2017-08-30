#!/bin/bash                                                                                                                                                                                                                                                                               
echo "Pretending to be systemctl. Args: $@"

if [[ "$1" == 'start' || "$1" == 'restart' ]]; then
  /usr/sbin/grrd --config="$(ls /usr/lib/grr/grr_*_amd64/grrd.yaml)" </dev/null &>/dev/null &
  echo "Started GRR client in the background."
fi
