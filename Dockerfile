# A Docker container capable of running all GRR components.
#
# Run the container with:
#
# docker run \
#    -e EXTERNAL_HOSTNAME="localhost" \
#    -e ADMIN_PASSWORD="demo" \
#    -p 0.0.0.0:8000:8000 \
#    -p 0.0.0.0:8080:8080 \
#    grrdocker/grr

FROM ubuntu:xenial

LABEL maintainer="grr-dev@googlegroups.com"

ARG COMMIT_SHA
ARG COMMIT_TIMESTAMP_SECS

ENV GRR_VENV /usr/share/grr-server
ENV PROTOC /usr/share/protobuf/bin/protoc
ENV PATH /opt/google-cloud-sdk/bin:${PATH}

SHELL ["/bin/bash", "-c"]

RUN apt-get update && \
  apt-get install -y \
  debhelper \
  default-jre \
  dpkg-dev \
  git \
  libffi-dev \
  libssl-dev \
  python-dev \
  python-pip \
  rpm \
  wget \
  zip

RUN pip install --upgrade pip virtualenv

# Install proto compiler
RUN mkdir -p /usr/share/protobuf && \
cd /usr/share/protobuf && \
wget --quiet "https://github.com/google/protobuf/releases/download/v3.3.0/protoc-3.3.0-linux-x86_64.zip" && \
unzip protoc-3.3.0-linux-x86_64.zip

# Make sure Bower will be able to run as root.
RUN echo '{ "allow_root": true }' > /root/.bowerrc

RUN virtualenv $GRR_VENV

RUN $GRR_VENV/bin/pip install --upgrade wheel six setuptools nodeenv

# TODO(ogaro) Stop hard-coding the node version to install
# when a Linux node-sass binary compatible with node v8.0.0 is
# available: https://github.com/sass/node-sass/pull/1969
RUN $GRR_VENV/bin/nodeenv -p --prebuilt --node=7.10.0

# Copy the GRR code over.
ADD . /usr/src/grr

RUN cd /usr/src/grr && mkdir /tmp/server-deb-files && docker/fetch_server_deb_tarball.sh /tmp/server-deb-files

WORKDIR /tmp/server-deb-files

RUN tar xzf *.tar.gz

RUN $GRR_VENV/bin/pip install --no-index \
    --find-links=grr/local_pypi \
    grr/local_pypi/grr-response-core-*.zip \
    grr/local_pypi/grr-response-client-*.zip \
    grr/local_pypi/grr-api-client-*.zip \
    grr/local_pypi/grr-response-server-*.zip \
    grr/local_pypi/grr-response-test-*.zip \
    grr/local_pypi/grr-response-templates-*.zip

# TODO(ogaro): Delete gcloud sdk and deb-files. Maybe pip cache too?

WORKDIR /

ENTRYPOINT ["/usr/src/grr/scripts/docker-entrypoint.sh"]

# Port for the admin UI GUI
EXPOSE 8000

# Port for clients to talk to
EXPOSE 8080

# Server config, logs, sqlite db
VOLUME ["/etc/grr", "/var/log", "/var/grr-datastore"]

CMD ["grr"]
