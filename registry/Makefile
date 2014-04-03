build:
	docker build -t deis/registry .

install:
	vagrant ssh -c 'sudo systemctl enable /home/core/share/registry/systemd/*'

uninstall:
	vagrant ssh -c 'sudo systemctl disable /home/core/share/registry/systemd/*'

start:
	vagrant ssh -c 'sudo systemctl start deis-registry.service'

stop:
	vagrant ssh -c 'sudo systemctl stop deis-registry.service'

restart:
	vagrant ssh -c 'sudo systemctl restart deis-registry.service'

logs:
	vagrant ssh -c 'sudo journalctl -f -u deis-registry.service'

run: install restart logs

clean: stop uninstall
	-docker rm -f deis-registry
	-docker rmi deis/registry
