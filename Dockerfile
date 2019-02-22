FROM centos:7

RUN yum install -y epel-release
RUN yum install -y openssl-devel python36 && yum clean all
RUN python3.6 -m ensurepip && \
    python3.6 -m pip install -U pip

COPY . /src
RUN python3.6 -m pip install /src

COPY manifest.yaml /usr/share/manifest.yaml
