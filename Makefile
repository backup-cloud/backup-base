test: build
	behave --tags '~@future' features-mocked
	behave --tags '~@future'

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

