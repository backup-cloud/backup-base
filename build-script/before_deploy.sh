#!/bin/sh

# this prepares to deploy - it expects to be run in the base travis VM

# shellcheck disable=SC2154
openssl aes-256-cbc -K "$encrypted_c2402a3ad637_key" -iv "$encrypted_c2402a3ad637_iv" -in encrypted_build_files.tjz.enc -out encrypted_build_files.tjz -d
tar xjvf encrypted_build_files.tjz 
chmod 400 deploy_key
sh -vx ./push_on_success.sh
rm -f deploy_key
python3 setup.py sdist
git tag "${TRAVIS_TAG:-$(date +'%Y%m%d%H%M%S')-$(git log --format=%h -1)}"
