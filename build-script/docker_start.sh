#!/bin/sh

# run from travis.yml this starts up the docker image and maps the
# build driectory in to the container.  Obviously this doesn't get run
# with a docker exec command.

docker run -d --name backup-test -e LC_ALL="en_US.UTF-8" -e LANG="en_US.UTF-8" -v "$(pwd):/travis" -w /travis "$DOCKER_IMAGE" tail -f /dev/null
docker ps
