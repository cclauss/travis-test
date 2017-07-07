#!/bin/bash

set -e

DOCKER_USR=grrbot
DOCKER_IMG=travis_test

sudo docker build --tag "$DOCKER_IMG" --build-arg user="$DOCKER_USR" .

container_id=$(sudo docker create "$DOCKER_IMG")

sudo docker cp "$container_id:/home/$DOCKER_USR/protobuf/readme.txt" .

sudo docker rm "$container_id"

cat 'readme.txt'
