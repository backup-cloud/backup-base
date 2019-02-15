#!/bin/sh

# this prepares the docker container for the various build and test
# commands.  It expects to be run _inside_ the container (e.g. with
# docker exec).

# DISABLE: this is needed for ansible setup but in the case of Travis we currently prepare the account before the build.
# # shellcheck disable=SC2154
# openssl aes-256-cbc -K "$encrypted_c2402a3ad637_key" -iv "$encrypted_c2402a3ad637_iv" -in aws_credentials_travis.yml.enc -out aws_credentials_travis.yml -d
# shellcheck disable=SC2154
openssl aes-256-cbc -K "$encrypted_c2402a3ad637_key" -iv "$encrypted_c2402a3ad637_iv" -in encrypted_build_files.tjz.enc -out encrypted_build_files.tjz -d
tar xjvf encrypted_build_files.tjz 
# shellcheck disable=SC2154
echo "$test_random_key" > .anslk_random_testkey

