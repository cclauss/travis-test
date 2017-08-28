#!/bin/bash

set -e

INITIAL_DIR="${PWD}"
WORK_DIR=/tmp/docker_work_dir
GCLOUD_SDK_TARBALL='google-cloud-sdk-167.0.0-linux-x86_64.tar.gz'
GCLOUD_SDK_URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/${GCLOUD_SDK_TARBALL}"

COMMIT_SHA="$(git show -s --format=%H)"
COMMIT_TIMESTAMP_SECS="$(git show -s --format=%ct)"

# TODO(ogaro): Delete.
echo "Sha: ${COMMIT_SHA}. Timestamp: ${COMMIT_TIMESTAMP_SECS}"
COMMIT_SHA=1a631a36b5bff2dd561f91ecc03624900ebb7297
COMMIT_TIMESTAMP_SECS=1503482353

format_git_timestamp="
from datetime import datetime
print(datetime.utcfromtimestamp(
    ${COMMIT_TIMESTAMP_SECS}).strftime('%Y-%m-%dT%H:%MUTC'));
"

COMMIT_TIMESTAMP=$(python -c "${format_git_timestamp}")

GRR_TARBALL_URL="gs://autobuilds.grr-response.com/${COMMIT_TIMESTAMP}_${COMMIT_SHA}/travis_job_*_server_deb/grr-server_*.tar.gz"

if [[ -d "${WORK_DIR}" ]]; then
  echo 'Deleting existing directory: "${WORK_DIR}"'
  rm -rf "${WORK_DIR}"
fi
mkdir "${WORK_DIR}" && cd "${WORK_DIR}"

wget --quiet "${GCLOUD_SDK_URL}"
tar xzf "${GCLOUD_SDK_TARBALL}"

grr_tarball_exists="$((google-cloud-sdk/bin/gsutil --quiet stat "${GRR_TARBALL_URL}" && echo true) || echo false)"
if [[ "${grr_tarball_exists}" != 'true' ]]; then
  echo "GRR tarball not found: ${GRR_TARBALL_URL}"
  exit 2
fi

google-cloud-sdk/bin/gsutil cp "${GRR_TARBALL_URL}" .

tar xzf grr-server_*.tar.gz

$GRR_VENV/bin/pip install --no-index --no-cache-dir \
    --find-links=grr/local_pypi \
    grr/local_pypi/grr-response-core-*.zip \
    grr/local_pypi/grr-response-client-*.zip \
    grr/local_pypi/grr-api-client-*.zip \
    grr/local_pypi/grr-response-server-*.zip \
    grr/local_pypi/grr-response-test-*.zip \
    grr/local_pypi/grr-response-templates-*.zip

cd "${INITIAL_DIR}"
rm -rf "${WORK_DIR}"
