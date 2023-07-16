.RECIPEPREFIX +=

SHELL = /bin/bash

VERSION := latest

lint:
	eval "$(pyenv init -)"
	OBJECT_CLONER_DEV_DEPENDENCIES_ENABLED=true OBJECT_CLONER_VERSION=0.0.1 pip3 install src/
	pre-commit run --all-files

build:
	docker build -t maxnasonov/object-cloner:$(VERSION) -f docker/Dockerfile .

push: build
	echo ${DOCKER_HUB_PASSWORD} | docker login -u${DOCKER_HUB_USERNAME} --password-stdin
	docker push maxnasonov/object-cloner:$(VERSION)