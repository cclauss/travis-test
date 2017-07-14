#!/bin/bash

readonly DOCKER_USER=${DOCKER_USER:-grrbot}

install_prereqs() {
  yum install -y \
    emacs \
    epel-release \
    python-devel \
    wget \
    which \
    java-1.8.0-openjdk \
    libffi-devel \
    openssl-devel \
    zip \
    git \
    gcc \
    gcc-c++ \
    redhat-rpm-config \
    rpm-build \
    rpm-sign
  yum install -y python-pip
  pip install --upgrade virtualenv
}

set_up_mountdir_permissions() {
  # Group that owns the mounted GRR repo.
  mountdir_gid="$(stat -c '%g' /mnt)"
  mountdir_grp_exists="$(cat /etc/group | grep ${mountdir_gid} | wc -l)"

  # Create group in container if it does not exist.
  mountdir_gname='mntgrp'
  if [[ "${mountdir_grp_exists}" == '0' ]]; then
    groupadd -g "${mountdir_gid}" "${mountdir_gname}"
  else
    mountdir_gname="$(getent group ${mountdir_gid} | cut -d: -f1)"
  fi

  usermod -a -G "${mountdir_gname}" "${DOCKER_USER}"

  # Give the group owner write permission to the GRR repo.
  # Note that any changes the test user makes inside
  # the container will be reflected in the actual directory
  # outside the container.
  chmod -R g+w /mnt
}

install_prereqs

adduser -m "${DOCKER_USER}"

set_up_mountdir_permissions
