#!/bin/bash

# Write header row of log file.
echo "$(date) $(free -hmw | grep available)" >> /var/log/grr_e2e_mem_usage.log
# Install the crontab file.
cp "${APPVEYOR_BUILD_FOLDER}/appveyor/linux/grr_e2e_mem_usage.cron" /etc/cron.d/
systemctl restart cron
