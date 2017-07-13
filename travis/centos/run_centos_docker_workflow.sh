#!/bin/bash

set -e

#cd $HOME/grr

cd /mnt

export TRAVIS_OS_NAME=${TRAVIS_OS_NAME:-linux}

travis/install_protobuf.sh linux

virtualenv "$HOME/INSTALL"

export PROTOC=${PROTOC:-$HOME/protobuf/bin/protoc}

travis/install.sh

source "${HOME}/INSTALL/bin/activate"

grr_client_build build --output built_templates

grr_client_build --verbose --secondary_configs grr/config/grr-response-test/test_data/dummyconfig.yaml repack --template built_templates/*.zip --output_dir built_templates/
