#!/bin/bash

set -ex

apt install -y /usr/share/grr-server/executables/installers/grr_*_amd64.deb

CLIENT_ID="$(grr_console --code_to_execute 'from grr.test_lib import test_lib; print(test_lib.GetClientId("/etc/grr.local.yaml"))')"

echo "Installed GRR client [Id ${CLIENT_ID}]"

# Enable verbose logging and increase polling frequency so flows get picked up quicker.
echo -e "Logging.engines: stderr,file\nLogging.verbose: True\nClient.poll_max: 5" >> /etc/grr.local.yaml

systemctl restart grr
