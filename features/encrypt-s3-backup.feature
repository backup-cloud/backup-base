Feature: encrypt backup data using keys and information provided in SSM parameter store

In order provide secure backups of our data, paddle system engineering
team would like to have a system which takes public keys from S3,
based on a location given in SSM parameter store and uses that key to
upload and encrypted backup of our data to an S3 bucket.

    Background: we have prepared to run encrypted backups
          Given I have access to an account for doing backups
            and I have a private public key pair
            and the public key from that key pair is stored in an s3 bucket

    Scenario: store encrypted backup in S3
        Given I have configured my settings in SSM
          and I have a file in S3 to backup
          and I have a backup context configured with matching users
         When I request a backup of that file using the context
         Then a backup object should be created in the S3 destination bucket
          and if I decrypt that file the content with the private key it should match the original
    
    Scenario: store encrypted backup in S3 with slash ('/') prefixed s3_path
        Given I have configured my settings in SSM
          and I have a file in S3 to backup
          and I have a backup context configured with the s3_path starting with a '/'
         When I request a backup of that file using the context
         Then a backup object should be created in the S3 destination bucket
          and the object path should not contain extraneous slashes
          and if I decrypt that file the content with the private key it should match the original

    @future
    Scenario: automatically store encrypted backup in S3 based on SSM settings
        Given I have a set of folders in S3 containing some objects
          and I have a file in my configuration directory with a list of those s3 folders
         When I run my backup script giving it the base path in SSM
         Then backup objects should be created in the S3 destination bucket
          and if I decrypt any of those files the content with the private key it should match the original

    @future
    Scenario: store encrypted backup in S3 using a container
        Given I have configured a base path in SSM
          and I have configured a public key and a reference to it
          and I have an S3 backup bucket where I have write access
          and I have a file in S3 to backup
         When I run my backup container giving the base path
         Then a backup should be created in the S3 destination bucket
          and backup should contain my data

    @future
    Scenario: store encrypted backup in S3 using an EC2 instance
        Given I have configured a base path in SSM
          and I have configured a public key and a reference to it
          and I have an S3 backup bucket where I have write access
          and I have a file in S3 to backup
         When I run my backup container giving the base path
         Then a backup should be created in the S3 destination bucket
          and backup should contain my data
