#!/bin/bash

set -e

TIMEOUT_SECS=3600
GCS_POLL_INTERVAL_SECS=30
LOCAL_TEMPLATE_DIR='grr/config/grr-response-templates/templates'

commit_timestamp_secs="$(git show -s --format=%ct "${TRAVIS_COMMIT}")"
# Hacky, but platform independent way of formatting the timestamp.
pyscript="
from datetime import datetime
print(datetime.utcfromtimestamp(
    ${commit_timestamp_secs}).strftime('%Y-%m-%dT%H:%MUTC'));
"
commit_timestamp=$(python -c "${pyscript}")
COMMIT_DIR="gs://${GCS_BUCKET}/${commit_timestamp}_${TRAVIS_COMMIT}"

declare -A remote_templates
remote_templates['windows_64bit_template']='appveyor_build_*_job_1/GRR_*_amd64.exe.zip'
remote_templates['windows_32bit_template']='appveyor_build_*_job_1/GRR_*_i386.exe.zip'
remote_templates['debian_64bit_template']='travis_job_*_ubuntu_64bit/grr_*_amd64.deb.zip'
remote_templates['debian_32bit_template']='travis_job_*_ubuntu_32bit/grr_*_i386.deb.zip'
remote_templates['centos_64bit_template']='travis_job_*_centos_64bit/grr_*_amd64.rpm.zip'
remote_templates['centos_32bit_template']='travis_job_*_centos_32bit/grr_*_i386.rpm.zip'
remote_templates['osx_template']='travis_job_*_osx/grr_*_amd64.xar.zip'

if [[ ! -d "${LOCAL_TEMPLATE_DIR}" ]]; then
  mkdir "${LOCAL_TEMPLATE_DIR}"
fi

poll_start=$(date +%s)
while true; do
  for template in "${!remote_templates[@]}"; do
    template_path="${remote_templates[$template]}"
    template_ready="$((gsutil --quiet stat "${COMMIT_DIR}/${template_path}" && echo true) || echo false)"
    if [[ "${template_ready}" == 'true' ]]; then
      gsutil cp "${COMMIT_DIR}/${template_path}" "${LOCAL_TEMPLATE_DIR}"
      unset remote_templates["${template}"]
    else
      echo "${template} is not ready"
    fi
  done
  num_templates_remaining=${#remote_templates[@]}
  secs_elapsed=$(expr $(date +%s) - $poll_start)  
  if [[ $num_templates_remaining -eq 0 ]]; then
    echo 'All templates downloaded'
    break
  elif [[ $secs_elapsed -gt $TIMEOUT_SECS ]]; then
    echo "Timeout of ${TIMEOUT_SECS} seconds has been exceeded"
    exit 1
  else
    echo "${num_templates_remaining} templates left. Sleeping for ${GCS_POLL_INTERVAL_SECS} seconds.."
    sleep $GCS_POLL_INTERVAL_SECS
  fi
done
