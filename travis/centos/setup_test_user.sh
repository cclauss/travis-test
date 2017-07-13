#!/bin/bash

adduser -m grrbot
TARGET_GID=$(stat -c "%g" /mnt)

EXISTS=$(cat /etc/group | grep $TARGET_GID | wc -l)

# Create new group using target GID and add nobody user
if [ $EXISTS == "0" ]; then
  groupadd -g $TARGET_GID mntgroup
  usermod -a -G mntgroup grrbot
else
  # GID exists, find group name and add
  GROUP=$(getent group $TARGET_GID | cut -d: -f1)
  usermod -a -G $GROUP grrbot
fi

chmod -R g+w /mnt
