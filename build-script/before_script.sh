#!/bin/sh

# this prepares the general build environment - it expects to be run
# in the base travis VM

# shellcheck disable=SC2154
openssl aes-256-cbc -K "$encrypted_c2402a3ad637_key" -iv "$encrypted_c2402a3ad637_iv" -in encrypted_build_files.tjz.enc -out encrypted_build_files.tjz -d
tar xjvf encrypted_build_files.tjz 
# shellcheck disable=SC2154
echo "$test_random_key" > .anslk_random_testkey
