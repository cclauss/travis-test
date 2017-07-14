#!/bin/bash
#
# This is run in the 'before_install' stage of Travis builds.

readonly CENTOS_DOCKER_IMG=${CENTOS_DOCKER_IMG:-centos:7}
readonly CENTOS_DOCKER_CONTAINER=${CENTOS_DOCKER_CONTAINER:-grr_container}

# Create a centos container which mounts the GRR repo in the
# /mnt directory.
docker create \
  -it \
  -v "${PWD}:/mnt" \
  --name "${CENTOS_DOCKER_CONTAINER}" \
  "${CENTOS_DOCKER_IMG}"

docker start "${CENTOS_DOCKER_CONTAINER}"
docker exec "${CENTOS_DOCKER_CONTAINER}" /mnt/travis/centos/set_up_docker_container.sh
