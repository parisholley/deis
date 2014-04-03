build:
	docker build -t deis/database .

install:
	vagrant ssh -c 'sudo systemctl enable /home/core/share/database/systemd/*'

uninstall:
	vagrant ssh -c 'sudo systemctl disable /home/core/share/database/systemd/*'

start:
	vagrant ssh -c 'sudo systemctl start deis-database.service'

stop:
	vagrant ssh -c 'sudo systemctl stop deis-database.service'

restart:
	vagrant ssh -c 'sudo systemctl restart deis-database.service'

logs:
	vagrant ssh -c 'sudo journalctl -f -u deis-database.service'

run: install restart logs

clean: stop uninstall
	-docker rm -f deis-database
	-docker rmi deis/database
