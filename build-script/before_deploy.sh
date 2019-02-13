#!/bin/sh

# this prepares to deploy - it expects to be run in the base travis VM

# shellcheck disable=SC2154
openssl aes-256-cbc -K "$encrypted_a45cc096e026_key" -iv "$encrypted_a45cc096e026_iv" -in deploy_key.enc -out deploy_key -d
chmod 400 deploy_key
./push_on_success.sh
rm deploy_key
python3 setup.py sdist
git tag "${TRAVIS_TAG:-$(date +'%Y%m%d%H%M%S')-$(git log --format=%h -1)}"
