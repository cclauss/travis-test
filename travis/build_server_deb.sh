#!/bin/bash

set -e

TRAVIS_COMMIT=${TRAVIS_COMMIT:-$(git show -s --format='%H' HEAD)}

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

create_changelog
export_build_vars
dpkg-buildpackage -us -uc

# TODO(ogaro): Rename the upload directory.
mkdir built_templates && cp $PWD/../grr-server* built_templates
