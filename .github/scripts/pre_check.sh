#! /bin/bash
# This script is used in release-it as hook
# Change how this script is triggered by editing .release-it.json
# NOTE: Please make sure working directory is in root of repo

set -e

file_list=$(cat .github/files_to_copy)
for f in $file_list
do
    echo "**** checking $f ****"
    if [ ! -f $f ] && [ ! -d $f ]; then
      echo "**** $f doesn't exist, skipping release ****"
      exit 1
    fi
done

echo "**** pre-check is finished ****"