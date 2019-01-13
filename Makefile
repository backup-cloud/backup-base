test: build
	behave --tags '~@future' features-mocked
	behave --tags '~@future'

prepare: .prepare_complete

.prepare_complete: prepare-account.yml prepare-test-enc-backup.yml
	ansible-playbook -vvv prepare-account.yml
	ansible-playbook -vvv prepare-test-enc-backup.yml
	touch .prepare_complete

wip: build
	behave --wip features-mocked
	behave --wip

build: lint 

lint:
	./lint-all-the-files.sh


testfix:
	find . -name '*.py' | xargs black --line-length=100 --diff

fix:
	find . -name '*.py' | xargs black --line-length=100 

.PHONY: build

