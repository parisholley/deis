build:
	docker build -t deis/cache .

install:
	vagrant ssh -c 'sudo systemctl enable /home/core/share/cache/systemd/*'

uninstall: stop
	vagrant ssh -c 'sudo systemctl disable /home/core/share/cache/systemd/*'

start:
	vagrant ssh -c 'sudo systemctl start deis-cache.service'

stop:
	vagrant ssh -c 'sudo systemctl stop deis-cache.service'

restart:
	vagrant ssh -c 'sudo systemctl restart deis-cache.service'

logs:
	vagrant ssh -c 'sudo journalctl -f -u deis-cache.service'

run: install restart logs

clean: uninstall
	-docker rm -f deis-cache

full-clean: clean
	-docker rmi deis/cache
