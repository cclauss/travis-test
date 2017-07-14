#!/bin/bash
#
# This is run in the 'install' stage of Travis builds.

set -e

cd /mnt

export TRAVIS_OS_NAME=${TRAVIS_OS_NAME:-linux}
export PROTOC=${PROTOC:-$HOME/protobuf/bin/protoc}

travis/install_protobuf.sh linux

virtualenv "$HOME/INSTALL"

travis/install.sh
