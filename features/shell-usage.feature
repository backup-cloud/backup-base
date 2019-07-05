Feature: make system easily available in shell scripts
In order to use the backup context easily in shell scripts there
should be a command which can be run and provides the definitions
needed.

  Background: we have prepared to run encrypted backups
        Given I have access to an account for doing backups
          and I have a private public key pair
          and the public key from that key pair is stored in an s3 bucket

  @wip
  @mocked
  Scenario: run backup from a script
      Given that I have prepared my account with definitions for backups
        and that I have a file in my directory
        and that I have a shell script which calls the backup command and encrypts that file
       When I run that script 
       Then an encrypted file should be created
