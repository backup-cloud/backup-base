#!/bin/sh

# this prepares the docker container for the various build and test
# commands.  It expects to be run _inside_ the container (e.g. with
# docker exec) and in the base directory of the repo.

apt-get update
apt-get install -y software-properties-common make git python3.7 python3-pip shellcheck libgpgme11 python3-gpg shellcheck
add-apt-repository -y ppa:ansible/ansible-2.7
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -y ansible python-pip python-boto3
make pip_install
python --version; echo ; python2 --version ; python3 --version
pre-commit install --install-hooks
