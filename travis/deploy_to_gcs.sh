#!/bin/bash

set -e

commit_timestamp_secs="$(git show -s --format=%ct "${TRAVIS_COMMIT}")"

# Hacky, but platform independent way of formatting the timestamp.
pyscript="
from datetime import datetime
print(datetime.utcfromtimestamp(
    ${commit_timestamp_secs}).strftime('%Y-%m-%dT%H:%MUTC'));
"
commit_timestamp=$(python -c "${pyscript}")

gcs_dest="gs://${GCS_BUCKET}/${commit_timestamp}_${TRAVIS_COMMIT}/travis_job_${TRAVIS_JOB_NUMBER}_${GCS_TAG}/"

echo Uploading templates to "${gcs_dest}"
gsutil -m cp gcs_upload_dir/* "${gcs_dest}"

if [[ "$TRAVIS_OS_NAME" == "linux" ]]; then
  shred -u travis/travis_uploader_service_account.json
fi
if [[ "$TRAVIS_OS_NAME" == "osx" ]]; then
  srm -sz travis/travis_uploader_service_account.json
fi

if [[ "${GCS_TAG}" != 'server_deb' ]]; then
  exit 0
fi

# Bail if the server deb wasn't built.
if [[ -z "$(ls gcs_upload_dir/grr-server_*_amd64.deb 2>/dev/null)" ]]; then
  echo 'Server deb not found in gcs_upload_dir'
  exit 1
fi

gsutil rm -r gs://${GCS_BUCKET}/_server_deb_temp/ || true

gsutil -m cp gcs_upload_dir/* gs://${GCS_BUCKET}/_server_deb_temp

gsutil rm -r gs://${GCS_BUCKET}/_latest_server_deb/ || true

gsutil -m cp gs://${GCS_BUCKET}/_server_deb_temp/* gs://${GCS_BUCKET}/_latest_server_deb

# Trigger build of a new GRR Docker image (grrdocker/grr)
# See https://hub.docker.com/r/grrdocker/grr/~/settings/automated-builds/
curl -H "Content-Type: application/json" --data '{"docker_tag": "latest"}' -X POST https://registry.hub.docker.com/u/grrdocker/grr/trigger/4499c4d4-4a8b-48da-bc95-5dbab39be545/
