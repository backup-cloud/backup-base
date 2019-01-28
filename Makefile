KEYFILE =.anslk_random_testkey
ifeq (,$(wildcard $(KEYFILE)))
  $(error "no key present - run `make prepare' to build test environment")
endif

ifeq (,$(AWS_ACCOUNT_NAME))
  AWS_ACCOUNT_NAME = michael
endif

# these variables cannot be immediate since running the prepare target
# may change the values.
RANDOM_KEY = $(shell cat $(KEYFILE))
export RANDOM_KEY
S3_TEST_BUCKET = test-backup-$(RANDOM_KEY)
export S3_TEST_BUCKET

all: prepare lint build test

test: build
	if [ '!' -f $${KEYFILE} ] ;\
	then \
		echo "file: $(KEYFILE) missing - run make prepare first" ; \
		exit 5 ; \
	fi
	if [ -z $${RANDOM_KEY} ] ; \
	then \
		echo 'no RANDOM_KEY found - N.B. be sure you are using a recent gmake!!! run *make prepare* to build test environment.'  ; \
		exit 5 ; \
	fi
	# echo "********** environment **********"
	# env
	# echo "*********************************"
	python -m pytest -vv tests
	behave --tags '~@future' features-mocked
	behave --tags '~@future'
	python -m doctest -v README.md

init:
	pip install -r requirements.txt

prepare: .prepare_complete

.prepare_complete: prepare-account prep_test
	touch .prepare_complete

prepare-account: prepare-account.yml
	ansible-playbook -vvv prepare-account.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

prep_test: prepare-test-enc-backup.yml
	ansible-playbook -vvv prepare-test-enc-backup.yml --extra-vars=aws_account_name=$(AWS_ACCOUNT_NAME)

wip: build
	behave --wip features-mocked
	behave --wip

build:

lint:
	./lint-all-the-files.sh

testfix:
	find . -name '*.py' | xargs black --line-length=100 --diff

fix:
	find . -name '*.py' | xargs black --line-length=100 

.PHONY: all test init prepare prep_test prepare_account wip build lint testfix fix

