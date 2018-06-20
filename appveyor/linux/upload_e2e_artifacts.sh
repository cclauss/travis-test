#!/bin/bash

mkdir server-configs server-logs client-configs client-logs
sudo cp /usr/share/grr-server/install_data/etc/grr-server.yaml server-configs || true # Primary server config.
sudo cp /etc/grr/server.local.yaml server-configs || true # Server writeback.
sudo cp /usr/share/grr-server/lib/python2.7/site-packages/grr/var/log/* server-logs || true
sudo cp /usr/lib/grr/grr_*_amd64/grrd.yaml client-configs || true # Primary client config.
sudo cp /etc/grr.local.yaml client-configs || true # Secondary client config.
sudo cp /var/log/GRRlog.txt client-logs || true

# Give read permissions to the non-root user.
sudo chown -R "$(whoami)" server-configs server-logs client-configs client-logs

appveyor PushArtifact e2e.log -DeploymentName 'Test Output'

for cfg in "$(ls server-configs)"; do
  appveyor PushArtifact "server-configs/${cfg}" -DeploymentName 'Server Configs'
done
