from cStringIO import StringIO
import base64
import os
import random
import subprocess


ROOT_DIR = os.path.join(os.getcwd(), 'coreos')
if not os.path.exists(ROOT_DIR):
    os.mkdir(ROOT_DIR)


class FleetClient(object):

    def __init__(self, cluster_name, hosts, auth):
        self.name = cluster_name
        self.hosts = hosts
        self.auth = auth
        self.auth_path = os.path.join(ROOT_DIR, 'ssh-{cluster_name}'.format(**locals()))
        with open(self.auth_path, 'w') as f:
            f.write(base64.b64decode(auth))
            os.chmod(self.auth_path, 0600)
        self.env = {
            'PATH': '/usr/local/bin:/usr/bin:/bin:{}'.format(
                os.path.abspath(os.path.join(__file__, '..'))),
            'FLEETW_KEY': self.auth_path,
            'FLEETW_HOST': random.choice(self.hosts.split(','))}

    # scheduler setup / teardown

    def setUp(self):
        """
        Setup a CoreOS cluster including router and log aggregator
        """
        self._create_router()
        self._create_logger()

    def _create_router(self, name='deis-router', image='deis/router'):
        self.create(name, image, template=ROUTER_TEMPLATE)
        self.start(name)

    def _create_logger(self, name='deis-logger', image='deis/logger'):
        self.create(name, image, template=LOGGER_TEMPLATE)
        self.start(name)

    def tearDown(self):
        """
        Tear down a CoreOS cluster including router and log aggregator
        """
        self.destroy('deis-router')
        self.destroy('deis-logger')

    # job api

    def create(self, name, image, command='', template=None):
        """
        Create a new job
        """
        print 'Creating {name}'.format(**locals())
        env = self.env.copy()
        self._create_container(name, image, command, env)
        self._create_announcer(name, image, command, env)

    # TODO: remove hardcoded ports

    def _create_container(self, name, image, command, env, port=5000):
        env.update({'FLEETW_UNIT': name + '.service'})
        env.update({'FLEETW_UNIT_DATA': base64.b64encode(CONTAINER_TEMPLATE.format(**locals()))})
        return subprocess.check_call('fleetctl.sh submit {name}.service'.format(**locals()),
                                     shell=True, env=env)

    def _create_announcer(self, name, image, command, env, port=5000):
        env.update({'FLEETW_UNIT': name + '-announce' + '.service'})
        env.update({'FLEETW_UNIT_DATA': base64.b64encode(ANNOUNCE_TEMPLATE.format(**locals()))})
        return subprocess.check_call('fleetctl.sh submit {name}-announce.service'.format(**locals()),  # noqa
                                     shell=True, env=env)

    def start(self, name):
        """
        Start an idle job
        """
        print 'Starting {name}'.format(**locals())
        env = self.env.copy()
        self._start_container(name, env)
        self._start_announcer(name, env)

    def _start_container(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh start {name}.service'.format(**locals()),
            shell=True, env=env)

    def _start_announcer(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh start {name}-announce.service'.format(**locals()),
            shell=True, env=env)

    def stop(self, name):
        """
        Stop a running job
        """
        print 'Stopping {name}'.format(**locals())
        env = self.env.copy()
        self._stop_announcer(name, env)
        self._stop_container(name, env)

    def _stop_container(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh stop {name}.service'.format(**locals()),
            shell=True, env=env)

    def _stop_announcer(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh stop {name}-announce.service'.format(**locals()),
            shell=True, env=env)

    def destroy(self, name):
        """
        Destroy an existing job
        """
        print 'Destroying {name}'.format(**locals())
        env = self.env.copy()
        self._destroy_announcer(name, env)
        self._destroy_container(name, env)

    def _destroy_container(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh destroy {name}.service'.format(**locals()),
            shell=True, env=env)

    def _destroy_announcer(self, name, env):
        return subprocess.check_call(
            'fleetctl.sh destroy {name}-announce.service'.format(**locals()),
            shell=True, env=env)

    def run(self, name, image, command):
        """
        Run a one-off command
        """
        print 'Running {name}'.format(**locals())
        output = subprocess.PIPE
        p = subprocess.Popen('fleetrun.sh {command}'.format(**locals()), shell=True, env=self.env,
                             stdout=output, stderr=subprocess.STDOUT)
        rc = p.wait()
        return rc, p.stdout.read()

    def attach(self, name):
        """
        Attach to a job's stdin, stdout and stderr
        """
        return StringIO(), StringIO(), StringIO()

SchedulerClient = FleetClient


CONTAINER_TEMPLATE = """
[Unit]
Description={name}
After=docker.service
Requires=docker.service

[Service]
ExecStartPre=/bin/sh -c "/usr/bin/docker pull {image}"  # noqa
ExecStart=/bin/bash -c '/usr/bin/docker run --name {name} -P -e PORT={port} -e ETCD=172.17.42.1:4001 --rm {image} {command} | logger -p local0.info -t {name} --tcp --server $(etcdctl get /deis/logger/host) --port $(etcdctl get /deis/logger/port)'  # noqa
ExecStop=/bin/bash -c '/usr/bin/docker stop {name} || /usr/bin/docker rm {name}'
"""

ROUTER_TEMPLATE = """
[Unit]
Description=Deis Router
After=docker.service
Requires=docker.service

[Service]
ExecStart=/bin/bash -c '/usr/bin/docker run --name {name} -P -e ETCD=172.17.42.1:4001 {image} {command}'  # noqa
ExecStop=/usr/bin/docker stop {name}
"""

LOGGER_TEMPLATE = """
[Unit]
Description=Deis Logger
After=docker.service
Requires=docker.service

[Service]
ExecStart=/bin/bash -c '/usr/bin/docker run --name {name} -P -e ETCD=172.17.42.1:4001 {image} {command}'  # noqa
ExecStop=/usr/bin/docker stop {name}
"""

ANNOUNCE_TEMPLATE = """
[Unit]
Description={name} announce
BindsTo={name}.service

[Service]
ExecStartPre=/bin/sh -c "echo Waiting for TCP port; until /usr/bin/docker port {name} {port} >/dev/null 2>&1; do sleep 2; done; port=$(docker port {name} {port} | cut -d ':' -f2); until cat </dev/null>/dev/tcp/%H/$port; do sleep 1; done"  # noqa
ExecStart=/bin/sh -c "port=$(docker port {name} {port} | cut -d ':' -f2); while netstat -lnt | grep $port >/dev/null; do etcdctl set /deis/services/{name} %H:$port --ttl 60; sleep 45; done"  # noqa
ExecStop=/usr/bin/etcdctl rm --recursive /deis/services/{name}

[X-Fleet]
X-ConditionMachineOf={name}.service
"""
