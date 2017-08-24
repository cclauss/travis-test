# A Docker container capable of running all GRR components.
FROM ubuntu:xenial

LABEL maintainer="grr-dev@googlegroups.com"

SHELL ["/bin/bash", "-c"]

# Copy the GRR code over.
ADD . /usr/src/grr

WORKDIR /usr/src/grr

RUN docker/fetch_server_deb_tarball.sh .
