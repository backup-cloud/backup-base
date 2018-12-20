Feature: encrypt backup data using keys and information provided in SSM parameter store

In order provide secure backups of our data, paddle system engineering
team would like to have a system which takes public keys from S3,
based on a location given in SSM parameter store and uses that key to
upload and encrypted backup of our data to an S3 bucket.

    @wip
    Scenario: store encrypted backup in S3
    given that I have configured a base path in SSM
     and that I have configured a public key and a reference to it
     and that I have an S3 backup bucket where I have write access
     and that I have a file in S3 to backup
    when I run my backup script giving it the base path in SSM
    then a backup should be created in the S3 destination bucket
     and that backup should contain my data

    Scenario: store encrypted backup in S3 using a container
    given that I have configured a base path in SSM
     and that I have configured a public key and a reference to it
     and that I have an S3 backup bucket where I have write access
     and that I have a file in S3 to backup
    when I run my backup container giving the base path
    then a backup should be created in the S3 destination bucket
     and that backup should contain my data

    Scenario: store encrypted backup in S3 using an EC2 instance
    given that I have configured a base path in SSM
     and that I have configured a public key and a reference to it
     and that I have an S3 backup bucket where I have write access
     and that I have a file in S3 to backup
    when I run my backup container giving the base path
    then a backup should be created in the S3 destination bucket
     and that backup should contain my data