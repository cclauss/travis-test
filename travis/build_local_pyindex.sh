#!/bin/bash

set -e

function build_sdists() {
  if [[ -d sdists ]]; then
    echo "Removing existing sdists directory."
    rm -rf sdists
  fi

  # TODO(ogaro): Make docs?
  python setup.py --quiet sdist \
      --formats=zip \
      --dist-dir=$PWD/sdists \
      --no-make-docs \
      --no-sync-artifacts
  python api_client/python/setup.py --quiet sdist \
      --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-test/setup.py  --quiet sdist \
      --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-client/setup.py --quiet sdist \
      --formats=zip --dist-dir=$PWD/sdists
  #python grr/config/grr-response-templates/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-server/setup.py --quiet sdist \
      --formats=zip --dist-dir=$PWD/sdists
}

function download_packages() {
  if [[ -d local_pypi ]]; then
    echo "Removing existing local_pypi directory."
    rm -rf local_pypi
  fi

  pip download --dest=local_pypi sdists/grr-response-core-*.zip
  pip download --dest=local_pypi sdists/grr-api-client-*.zip
  pip download --dest=local_pypi sdists/grr-response-test-*.zip
  pip download --dest=local_pypi sdists/grr-response-client-*.zip
  #pip download --dest=local_pypi sdists/grr-response-templates-*.zip
  pip download --dest=local_pypi sdists/grr-response-server-*.zip
}

source "${HOME}/INSTALL/bin/activate"
build_sdists
download_packages