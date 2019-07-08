AWS_ACCOUNT_NAME ?= michael
AWS_DEFAULT_REGION ?= us-east-2
PYTHON ?= python3
BEHAVE ?= behave
KEYFILE ?=.anslk_random_testkey

export AWS_DEFAULT_REGION

# these variables cannot be immediate since running the prepare target
# may change the values.
ifneq ($(wildcard $(KEYFILE)),)
  RANDOM_KEY = $(shell cat $(KEYFILE))
endif
S3_TEST_BUCKET = test-backup-$(RANDOM_KEY)
export RANDOM_KEY
export S3_TEST_BUCKET

all: prepare lint build test

test: build pytest behave doctest

behave: develop checkvars
	$(BEHAVE) --tags '~@future' features-mocked
	$(BEHAVE) --tags '~@future'



# develop is needed to install scripts that are called during testing 
develop: .develop.makestamp

.develop.makestamp: setup.py backup_cloud/shell_start.py
	$(PYTHON) setup.py develop
	touch $@

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
	$(PYTHON) -m pip install -r requirements.txt

# shellcheck does not exist yet on alpine so we skip that.

apk_install: apk_packages_install init

apk_packages_install:
	apk update
	apk add python3 py3-gpgme ansible openssl

deb_install: deb_packages_install init

deb_packages_install:
	apt-get update
	apt-get install -y software-properties-common
	add-apt-repository -y ppa:ansible/ansible-2.7
	apt-get update
	apt-get install -y python3.7 python3-pip shellcheck libgpgme11 python3-gpg shellcheck
	DEBIAN_FRONTEND=noninteractive apt-get install -y ansible python-pip python-boto3
	$(PYTHON_REQS)


prepare: encrypted_build_files.tjz.enc

ENC_DIR=encrypted_build_files
ENC_FILENAMES=aws_credentials.demo.env aws_credentials.env aws_credentials_travis.yml deploy_key
ENC_FILES := $(addprefix $(ENC_DIR)/,$(ENC_FILENAMES))

encrypted_build_files.tjz: prepare-account prep_test $(ENC_FILES)
	tar cvvjf $@ -C $(ENC_DIR) $(ENC_FILENAMES)

encrypted_build_files.tjz.enc: encrypted_build_files.tjz
	travis encrypt-file --force --no-interactive --org $<

prepare-account: prepare-account.yml
	ansible-playbook -vvv prepare-account.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

prep_test: prepare-test-enc-backup.yml
	ansible-playbook -vvv prepare-test-enc-backup.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

wip: develop build
	$(BEHAVE) --wip features-mocked
	$(BEHAVE) --wip

build:

lint:
	./lint-all-the-files.sh

testfix:
	find . -name '*.py' | xargs black --line-length=100 --diff

fix:
	find . -name '*.py' | xargs black --line-length=100 
.PHONY: all develop test behave checkvars pytest doctest init deb_install apk_install prepare prep_test prepare_account wip build lint testfix fix clean
