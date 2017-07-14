#!/bin/bash
#
# This is run in the 'script' stage of Travis builds.

set -e

cd /mnt

source "${HOME}/INSTALL/bin/activate"

grr_client_build build --output built_templates

grr_client_build \
  --verbose \
  --secondary_configs grr/config/grr-response-test/test_data/dummyconfig.yaml \
  repack \
  --template built_templates/*.zip \
  --output_dir built_templates
