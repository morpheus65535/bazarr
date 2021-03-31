#! /bin/bash
# This script is used in release-it as hook
# Change how this script is triggered by editing .release-it.json
# NOTE: Please make sure working directory is in root of repo
# NOTE: This script is only working on linux

set -e

# Get version from tag
git describe --abbrev=0 > VERSION

# Copy files based on files_to_copy
to_dist=__builds__/bazarr
mkdir -p $to_dist
file_list=$(cat .github/files_to_copy)
for f in $file_list
do
    echo "**** copying $f to release ****"
    cp -r --parents $f $to_dist
done

pushd __builds__/bazarr
zip -r ../bazarr.zip . -x '*.map' -b $(mktemp -d)
popd
rm -rf $to_dist