#!/bin/bash

python3 "${ROOT_DIRECTORY}"/bazarr.py --no-update &
PID=$!

sleep 30

if kill -s 0 $PID
then
  echo "Bazarr is still running. We'll test if UI is working..."
else
  exit 1
fi

exitcode=0
curl -fsSL --retry-all-errors --retry 60 --retry-max-time 120 --max-time 10 "http://127.0.0.1:6767" --output /dev/null || exitcode=$?
[[ ${exitcode} == 0 ]] && echo "UI is responsive, good news!" || echo "Oops, UI isn't reachable, bad news..."

echo "Let's stop Bazarr before we exit..."
pkill -INT -P $PID

exit ${exitcode}