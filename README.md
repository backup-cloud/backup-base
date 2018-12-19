This is a base layer for our automated backup which provides the
simple service of backing up from S3 locations into encrypted files in
other S3 locations.


Ansible based deployment
========================

There are three Ansible YAML files the first two are set up to be run
manually.

      - prepare-account.yml - this is for setting up accounts needed for other parts
      - deploy.yml - this is for deployment and is to be driven by CI/CD

The other one is expected to be run automatically during BDD testing. 

      - test-enc-backup.yml - part of the tests of the system included here



