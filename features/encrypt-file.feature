Feature: encrypt backup data using keys and information provided in SSM parameter store
In order to allow simple and secure handling of data we would like to
have a standard easy way to set up backup encryption

    Background: we have prepared to run encrypted backups
    given I have a private public key pair
      and the public key from that key pair is stored in the bucket

    @wip
    Scenario: check that we correctly encrypt a file
    given that I have a file in my directory
      and that I have a backup context configured
     when I run a script that calls my encryption command on that file
     then an encrypted file should be created
      and if I decrypt that file the content should match the original
