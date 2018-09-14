PHONY = venv

export SHELL := /bin/bash

PROJECT ?= gpXmlMidi
export PROJECT

# config locations
REQUIREMENTS := requirements.txt
REQ_FILES := $(REQUIREMENTS)

# command aliases
VIRTUAL_ENV ?= local
BIN := $(VIRTUAL_ENV)/bin
PIP := $(BIN)/pip3
PYTHON := $(BIN)/python3

_mkvenv:
	@echo "Creating the $(PROJECT) virtual env ..."
	source /usr/local/bin/virtualenvwrapper.sh && \
	mkvirtualenv $(PROJECT)

_update_venv_tools:
	$(PIP) install -U pip wheel setuptools

venv:
	virtualenv -p /usr/local/bin/python3 local
	$(PIP) install --upgrade pip wheel setuptools
	CFLAGS=-O0 $(PIP) install -r requirements.txt
	cp music21.rc ~/.music21rc

update_tools:
	$(PIP) install --upgrade pip wheel setuptools

update_reqs:
	$(PIP) install -r requirements.txt

mkvenv:
	@echo "Checking if the $(PROJECT) virtualenv exists ..."
	test -d $(VIRTUAL_ENV) || $(MAKE) _mkvenv $(MAKE) _update_venv_tools

$(REQ_FILES): FORCE
	@echo "Installing $@ requirements file ..."
	$(PIP) install $(PIP_INSTALL_ARGS) -r $@

clean: clean-pyc clean-pycache

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

clean-pycache:
	find . -iname "__pycache__" -exec rm -rf {} +

print-%: ; @echo $*=$($*)
