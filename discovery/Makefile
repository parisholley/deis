build:
	docker build -t deis/discovery .

install:
	vagrant ssh -c 'sudo systemctl enable /home/core/share/discovery/systemd/*'

uninstall:
	-vagrant ssh -c 'sudo systemctl disable /home/core/share/discovery/systemd/*'

start:
	vagrant ssh -c 'sudo systemctl start deis-discovery.service'

stop:
	-vagrant ssh -c 'sudo systemctl stop deis-discovery.service'

restart:
	vagrant ssh -c 'sudo systemctl restart deis-discovery.service'

logs:
	vagrant ssh -c 'sudo journalctl -f -u deis-discovery.service'

run: install restart logs

clean: stop uninstall
	-docker rm -f deis-discovery
	-docker rmi deis/discovery
