#!/bin/bash
#
# Fetches the latest server deb from Google Cloud Storage and installs it.
# This script needs root privileges to run.

set -ex

readonly CLOUD_SDK_REPO="cloud-sdk-$(lsb_release -c -s)"
readonly INITIAL_DIR="${PWD}"
readonly DEB_TEMPDIR=/tmp/grr_deb_install

if [[ -e "${DEB_TEMPDIR}" ]]; then
  rm -rf "${DEB_TEMPDIR}"
fi

mkdir "${DEB_TEMPDIR}"
cd "${DEB_TEMPDIR}"

pyscript="
import ConfigParser
config = ConfigParser.SafeConfigParser()
config.read('${APPVEYOR_BUILD_FOLDER}/version.ini')
print('%s.%s.%s-%s' % (
    config.get('Version', 'major'),
    config.get('Version', 'minor'),
    config.get('Version', 'revision'),
    config.get('Version', 'release')))
"
readonly DEB_VERSION="$(python -c "${pyscript}")"
readonly GCS_DEB_DIR="https://storage.googleapis.com/autobuilds.grr-response.com/_latest_server_deb"
wget "${GCS_DEB_DIR}/grr-server_${DEB_VERSION}_amd64.deb"
wget "${GCS_DEB_DIR}/grr-server_${DEB_VERSION}_amd64.changes"
wget "${GCS_DEB_DIR}/grr-server_${DEB_VERSION}.tar.gz"

echo -e ".changes file for downloaded server deb:\n\n$(cat grr-server_*_amd64.changes)\n"
DEBIAN_FRONTEND=noninteractive apt install -y ./grr-server_*_amd64.deb
grr_config_updater initialize --noprompt --external_hostname=localhost --admin_password="${GRR_ADMIN_PASS}"
echo 'Logging.verbose: True' >> /etc/grr/server.local.yaml
cp ${APPVEYOR_BUILD_FOLDER}/grr/server/grr_response_server/artifact_registry.py /usr/share/grr-server/lib/python2.7/site-packages/grr_response_server
cp ${APPVEYOR_BUILD_FOLDER}/grr/server/grr_response_server/flows/general/collectors.py /usr/share/grr-server/lib/python2.7/site-packages/grr_response_server/flows/general
apt update && apt install -y emacs
systemctl restart grr-server

echo "Installation of server deb completed."

tar xzf grr-server_*.tar.gz
source /usr/share/grr-server/bin/activate
pip install --no-index --find-links=grr/local_pypi grr/local_pypi/grr-response-test-*.zip
deactivate

cd "${INITIAL_DIR}"
