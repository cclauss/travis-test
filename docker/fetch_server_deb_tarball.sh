#!/bin/bash

set -e

SCRIPT_NAME=$(basename "$0")
if [[ $# != 1 ]]; then
  echo "Usage: ./${SCRIPT_NAME} [dest]"
  exit 1
fi

echo "Source commit is ${COMMIT_SHA}. Commit timestamp is ${COMMIT_TIMESTAMP_SECS}"

# TODO(ogaro): Delete.
top_commit=1a631a36b5bff2dd561f91ecc03624900ebb7297
commit_timestamp_secs=1503482353

pyscript="
from datetime import datetime
print(datetime.utcfromtimestamp(
    ${commit_timestamp_secs}).strftime('%Y-%m-%dT%H:%MUTC'));
"
commit_timestamp=$(python -c "${pyscript}")

if [[ "$(which gcloud)" ]]; then
  echo "Google Cloud SDK already installed"
  gcloud version
else
  echo "Google Cloud SDK not found. Downloading.."
  wget --quiet https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-167.0.0-linux-x86_64.tar.gz
  tar zxf google-cloud-sdk-167.0.0-linux-x86_64.tar.gz -C /opt
  rm google-cloud-sdk-167.0.0-linux-x86_64.tar.gz
fi

travis_tarball="gs://autobuilds.grr-response.com/${commit_timestamp}_${top_commit}/travis_job_*_server_deb/grr-server_*.tar.gz"
tarball_exists="$((gsutil --quiet stat "${travis_tarball}" && echo true) || echo false)"

if [[ "${tarball_exists}" != 'true' ]]; then
  echo "Server-deb tarball not found: ${travis_tarball}"
  exit 2
fi

gsutil cp "${travis_tarball}" "$1"
