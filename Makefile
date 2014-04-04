#
# Deis Makefile
#

# ordered list of deis components
COMPONENTS=registry logger database cache controller builder router

all: build run

test_client:
	python -m unittest discover client.tests

build:
	for c in $(COMPONENTS); do cd $$c && make build && cd ..; done

install:
	for c in $(COMPONENTS); do cd $$c && make install && cd ..; done

uninstall: stop
	-for c in $(COMPONENTS); do cd $$c ; make uninstall ; cd ..; done

start:
	for c in $(COMPONENTS); do cd $$c && make start && cd ..; done

stop:
	-for c in $(COMPONENTS); do cd $$c ; make stop ; cd ..; done

restart:
	for c in $(COMPONENTS); do cd $$c && make restart && cd ..; done

logs:
	vagrant ssh -c 'journalctl -f -u deis-*'

run: install restart logs

clean:
	-for c in $(COMPONENTS); do cd $$c && make clean ; cd ..; done

full-clean:
	-for c in $(COMPONENTS); do cd $$c && make full-clean ; cd ..; done
