KEYFILE =.anslk_random_testkey

AWS_ACCOUNT_NAME = michael
PYTHON = python
BEHAVE = behave

# these variables cannot be immediate since running the prepare target
# may change the values.
RANDOM_KEY = $(shell cat $(KEYFILE))
export RANDOM_KEY
S3_TEST_BUCKET = test-backup-$(RANDOM_KEY)
export S3_TEST_BUCKET

all: prepare lint build test

test: build pytest behave doctest

behave: checkvars
	$(BEHAVE) --tags '~@future' features-mocked
	$(BEHAVE) --tags '~@future'

checkvars:
	if [ '!' -f $${KEYFILE} ] ; then \
		echo "file: $(KEYFILE) missing - run make prepare first" ; exit 5 ; fi
	if [ -z $${RANDOM_KEY} ] ; then \
		echo 'no RANDOM_KEY found - N.B. be sure you are using a recent gmake!!! run *make prepare* to build test environment.'  ; exit 5 ; fi


pytest:
	$(PYTHON) -m pytest -vv tests

doctest:
	$(PYTHON) -m doctest -v README.md

init:
	pip install -r requirements.txt

# shellcheck does not exist yet on alpine so we skip that.

PYTHON_REQS := $(PYTHON) -m pip install -r requirements.txt

apk_install:
	apk update
	apk add python3 py3-gpgme ansible
	$(PYTHON_REQS)

deb_install:
	apt-get update
	apt-get install -y software-properties-common
	add-apt-repository -y ppa:ansible/ansible-2.7
	apt-get update
	apt-get install -y python3.7 python3-pip shellcheck python3-gpg shellcheck
	DEBIAN_FRONTEND=noninteractive apt-get install -y ansible python-pip python-boto3
	$(PYTHON_REQS)


prepare: .prepare_complete

.prepare_complete: prepare-account prep_test
	touch .prepare_complete

prepare-account: prepare-account.yml
	ansible-playbook -vvv prepare-account.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

prep_test: prepare-test-enc-backup.yml
	ansible-playbook -vvv prepare-test-enc-backup.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

wip: build
	$(BEHAVE) --wip features-mocked
	$(BEHAVE) --wip

build:

lint:
	./lint-all-the-files.sh

testfix:
	find . -name '*.py' | xargs black --line-length=100 --diff

fix:
	find . -name '*.py' | xargs black --line-length=100 

.PHONY: all test behave checkvars pytest doctest init deb_install apk_install prepare prep_test prepare_account wip build lint testfix fix clean

