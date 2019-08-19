#!/bin/sh

# this prepares the docker container for the various build and test
# commands.  It expects to be run _inside_ the container (e.g. with
# docker exec) and in the base directory of the repo.

apk update
apk add make python3 py3-gpgme ansible openssl
make pip_install
python --version; echo ; python2 --version ; python3 --version
