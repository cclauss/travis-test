#!/bin/bash

set -e

cd $HOME && git clone https://github.com/google/grr.git

cd $HOME/grr

export TRAVIS_OS_NAME=${TRAVIS_OS_NAME:-linux}

travis/install_protobuf.sh linux

virtualenv "$HOME/INSTALL" --python=/usr/local/bin/python2.7

export PROTOC=${PROTOC:-$HOME/protobuf/bin/protoc}

travis/install.sh

source "${HOME}/INSTALL/bin/activate"

grr_client_build build --output built_templates

grr_client_build build_components --output built_templates

grr_client_build --verbose --secondary_configs grr/config/grr-response-test/test_data/dummyconfig.yaml repack --template built_templates/*.zip --output_dir built_templates/
