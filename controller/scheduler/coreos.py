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

    def _create_router(self, name='deis-router', image='gabrtv/cache'):
        self.create(name, image, template=ROUTER_TEMPLATE)
        self.start(name)

    def _create_logger(self, name='deis-logger', image='gabrtv/cache'):
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
        template = CONTAINER_TEMPLATE if template is not None else template
        env.update({'FLEETW_UNIT': name + '.service',
                    'FLEETW_UNIT_DATA': base64.b64encode(CONTAINER_TEMPLATE.format(**locals())), })
        return subprocess.check_call(
            'fleetctl.sh submit {name}.service'.format(**locals()),
            shell=True, env=env)

    def start(self, name):
        """
        Start an idle job
        """
        print 'Starting {name}'.format(**locals())
        return subprocess.check_call(
            'fleetctl.sh start {name}.service'.format(**locals()),
            shell=True, env=self.env)

    def stop(self, name):
        """
        Stop a running job
        """
        print 'Stopping {name}'.format(**locals())
        return subprocess.check_call(
            'fleetctl.sh stop {name}.service'.format(**locals()),
            shell=True, env=self.env)

    def destroy(self, name):
        """
        Destroy an existing job
        """
        print 'Destroying {name}'.format(**locals())
        return subprocess.check_call(
            'fleetctl.sh destroy {name}.service'.format(**locals()),
            shell=True, env=self.env)

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
ExecStart=/bin/bash -c 'docker start -a {name} || docker run --name {name} -P -e ETCD=172.17.42.1:4001 {image}'  # noqa
ExecStop=/usr/bin/docker stop {name}
"""

ROUTER_TEMPLATE = """
[Unit]
Description=Deis Router
After=docker.service
Requires=docker.service

[Service]
ExecStart=/bin/bash -c 'docker start -a {name} || docker run --name {name} -P -e ETCD=172.17.42.1:4001 {image}'  # noqa
ExecStop=/usr/bin/docker stop {name}
"""

LOGGER_TEMPLATE = """
[Unit]
Description=Deis Logger
After=docker.service
Requires=docker.service

[Service]
ExecStart=/bin/bash -c 'docker start -a {name} || docker run --name {name} -P -e ETCD=172.17.42.1:4001 {image}'  # noqa
ExecStop=/usr/bin/docker stop {name}
"""
