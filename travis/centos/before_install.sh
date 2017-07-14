#!/bin/bash
#
# This is run in the 'before_install' stage of Travis builds.

readonly DOCKER_IMG=${DOCKER_IMG:-centos:7}
readonly DOCKER_CONTAINER=${DOCKER_CONTAINER:-grr_container}

# Create a Docker container which mounts the GRR repo in the
# /mnt directory.
docker create \
  -it \
  -v "${PWD}:/mnt" \
  --name "${DOCKER_CONTAINER}" \
  "${DOCKER_IMG}"

docker start "${DOCKER_CONTAINER}"
docker exec "${DOCKER_CONTAINER}" /mnt/travis/centos/set_up_docker_container.sh
