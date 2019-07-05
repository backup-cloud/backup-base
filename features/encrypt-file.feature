Feature: encrypt backup data using keys and information provided in SSM parameter store
In order to allow simple and secure handling of data we would like to
have a standard easy way to set up backup encryption

    Background: we have prepared to run encrypted backups
    given I have access to an account for doing backups

    Scenario: check that we correctly encrypt a file
    given I have a file in my directory
      and I have a private public key pair
      and the public key from that key pair is stored in an s3 bucket
      and I have a backup context configured with matching users
     when I run a script that calls my encryption command on that file
     then an encrypted file should be created
      and if I decrypt that file the content with the original GPG setup

    @future
    Scenario: check that we automatically find all default keys
    given I have a file in my directory
      and I have multiple key files configured
      and the public keys from those key pairs are stored in my s3 backup bucket
     when I configure a backup context 
      and I run a script that calls my encryption command on that file
     then an encrypted file should be created
      and I should be able to decrypt that file with each key provided

    @future
    Scenario: ignore non specified keys
    given I have a file in my directory
      and I have multiple key files configured
     when I configure a backup context specifyig one specific key
      and I run a script that calls my encryption command on that file
     then an encrypted file should be created
      but I should not be able to decrypt that file with the other keys
