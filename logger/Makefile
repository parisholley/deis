build:
	docker build -t deis/logger .

install:
	vagrant ssh -c 'sudo systemctl enable /home/core/share/logger/systemd/*'

uninstall: stop
	vagrant ssh -c 'sudo systemctl disable /home/core/share/logger/systemd/*'

start:
	vagrant ssh -c 'sudo systemctl start deis-logger.service'

stop:
	vagrant ssh -c 'sudo systemctl stop deis-logger.service'

restart:
	vagrant ssh -c 'sudo systemctl restart deis-logger.service'

logs:
	vagrant ssh -c 'sudo journalctl -f -u deis-logger.service'

run: install restart logs

clean: uninstall
	-docker rm -f deis-logger
	-docker rmi deis/logger
