FROM demonchild2112/grr_centos:7
LABEL maintainer="denver@ogaro.net"
ARG user
ENV GRR_USER=${user:-grrbot}
RUN useradd -m $GRR_USER
USER $GRR_USER
WORKDIR /home/$GRR_USER
RUN git clone https://github.com/google/grr.git
WORKDIR grr
RUN travis/install_protobuf.sh linux

