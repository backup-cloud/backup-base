#!/bin/sh

# this prepares the docker container for the various build and test
# commands.  It expects to be run _inside_ the container (e.g. with
# docker exec) and in the base directory of the repo.

apt update
apt -y install make git
make --trace deb_install PYTHON="$PYTHON"
python --version; echo ; python2 --version ; python3 --version
pre-commit install --install-hooks
