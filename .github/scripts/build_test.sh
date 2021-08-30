#!/bin/bash

python3 "${ROOT_DIRECTORY}"/bazarr.py &
PID=$!

sleep 30

if kill -s 0 $PID
then
  echo "Bazarr is still running. We'll kill it..."
  kill $PID
  exit 0
else
  exit 1
fi