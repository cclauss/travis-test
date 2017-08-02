#!/bin/bash

set -e

TRAVIS_COMMIT=${TRAVIS_COMMIT:-$(git show -s --format='%H' HEAD)}

function build_sdists() {
  if [[ -d sdists ]]; then
    echo "Removing existing sdists directory."
    rm -rf sdists
  fi

  # TODO(ogaro): Make docs?
  python setup.py sdist --formats=zip --dist-dir=$PWD/sdists --no-make-docs --no-sync-artifacts
  python api_client/python/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-test/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-client/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
  #python grr/config/grr-response-templates/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
  python grr/config/grr-response-server/setup.py sdist --formats=zip --dist-dir=$PWD/sdists
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

function create_changelog() {
  if [[ -f debian/changelog ]]; then
    echo "Replacing debian/changelog with new changelog."
    rm debian/changelog
  fi
  pyscript="
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read('version.ini')
print('%s.%s.%s-%s' % (
    config.get('Version', 'major'),
    config.get('Version', 'minor'),
    config.get('Version', 'revision'),
    config.get('Version', 'release')))
"
  deb_version="$(python -c "${pyscript}")"
  debchange --create \
      --newversion "${deb_version}" \
      --package grr-server \
      --urgency low \
      --controlmaint \
      --distribution unstable \
      "Autobuilt by Travis CI at ${TRAVIS_COMMIT}"
}

# Sets environment variables to be used by debhelper.
function export_build_vars() {
  # Note that versions for the packages listed here can differ.
  export LOCAL_DEB_PYINDEX="$PWD/local_pypi"
  export CORE_SDIST="$(ls sdists | grep -e 'grr-response-core-.*\.zip')"
  export API_SDIST="$(ls sdists | grep -e 'grr-api-client-.*\.zip')"
  export TEST_SDIST="$(ls sdists | grep -e 'grr-response-test-.*\.zip')"
  export CLIENT_SDIST="$(ls sdists | grep -e 'grr-response-client-.*\.zip')"
  #export TEMPLATES_SDIST="$(ls sdists | grep -e 'grr-response-templates-.*\.zip')"
  export SERVER_SDIST="$(ls sdists | grep -e 'grr-response-server-.*\.zip')"
}

source "${HOME}/INSTALL/bin/activate"
build_sdists
download_packages
create_changelog
export_build_vars
dpkg-buildpackage -us -uc

# TODO(ogaro): Rename the upload directory.
mkdir built_templates && cp $PWD/../grr-server* built_templates
