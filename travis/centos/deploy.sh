#!/bin/bash

set -e

pip install google-compute-engine

gcloud version || ( wget -q https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-116.0.0-linux-x86_64.tar.gz && tar zxf google-cloud-sdk-116.0.0-linux-x86_64.tar.gz -C "${HOME}" )

openssl aes-256-cbc \
  -K "${encrypted_b85fe3a43822_key}" \
  -iv "${encrypted_b85fe3a43822_iv}" \
  -in travis/centos/travis_uploader_service_account.json.enc \
  -out travis/centos/travis_uploader_service_account.json -d

gcloud auth activate-service-account --key-file travis/centos/travis_uploader_service_account.json
cloud_bucket="gs://ogaro-travis-test/${TRAVIS_JOB_NUMBER}"
echo "Uploading templates to ${cloud_bucket}"
gsutil -m cp built_templates/* "${cloud_bucket}"
shred -u travis/centos/travis_uploader_service_account.json
