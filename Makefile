test: build
	behave --tags '~@future'

wip: build
	behave --wip

build: lint container-test containers

lint:
	./lint-all-the-files.sh


testfix:
	find . -name '*.py' | xargs black --line-length=100 --diff
	# find . -name '*.py' | xargs autopep8 --aggressive --max-line-length=100 --diff

fix:
	find . -name '*.py' | xargs autopep8 --aggressive --max-line-length=100 --in-place

.PHONY: build

