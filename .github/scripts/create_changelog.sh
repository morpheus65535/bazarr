#! /bin/bash
# This script is used in release-it as changelog
# export RELEASE_MASTER=1 to release master changelog

set -e

master_version=$(git describe --tags --abbrev=0 --match "v[0-9].[0-9].[0-9]")
latest_verion=$(git describe --tags --abbrev=0)

if [[ $RELEASE_MASTER -eq 1 ]]; then
  auto-changelog --stdout --starting-version $master_version --commit-limit 3
else
  auto-changelog --stdout --starting-version $latest_verion --unreleased --commit-limit 0
fi