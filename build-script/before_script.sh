#!/bin/sh

# this prepares the docker container for the various build and test
# commands.  It expects to be run _inside_ the container (e.g. with
# docker exec).

$INSTALL_MAKE
$MAKE "$INSTALL_GOAL" PYTHON="$PYTHON"
python --version; echo ; python2 --version ; python3 --version
# shellcheck disable=SC2154
openssl aes-256-cbc -K "$encrypted_c2402a3ad637_key" -iv "$encrypted_c2402a3ad637_iv" -in aws_credentials_travis.yml.enc -out aws_credentials_travis.yml -d
# shellcheck disable=SC2154
echo "$test_random_key" > .anslk_random_testkey

