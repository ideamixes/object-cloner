.RECIPEPREFIX +=

SHELL = /bin/bash

TAG := latest
OBJECT_CLONER_VERSION ?= 0.0.1
ORG_NAME := ideamixes

lint:
	eval "$(pyenv init -)"
	OBJECT_CLONER_DEV_DEPENDENCIES_ENABLED=true OBJECT_CLONER_VERSION=$(OBJECT_CLONER_VERSION) pip3 install src/
	pre-commit run --all-files

build:
	docker build -t $(ORG_NAME)/object-cloner:$(TAG) --build-arg OBJECT_CLONER_VERSION=$(OBJECT_CLONER_VERSION) -f docker/Dockerfile .

push: build
	echo ${DOCKER_HUB_PASSWORD} | docker login -u${DOCKER_HUB_USERNAME} --password-stdin
	docker push $(ORG_NAME)/object-cloner:$(TAG)