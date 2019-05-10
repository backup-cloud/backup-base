This role is designed to prepare an account for testing with ansible
via a CI system.  It creates a user with limited rights which will be
fed into the CI system and prepares access keys for that user.

This role needs to be run with full privilages to set up an IAM user
and change policies which menas that it effectively must have full AWS
account privilages.  This means that it should typically _not_ be run
in the CI, instead just run once to set up the CI.
