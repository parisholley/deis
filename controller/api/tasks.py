"""
Long-running tasks for the Deis Controller API

This module orchestrates the real "heavy lifting" of Deis, and as such these
functions are decorated to run as asynchronous celery tasks.
"""

from __future__ import unicode_literals

from celery import task


@task
def create_cluster(cluster):
    cluster._scheduler.setUp()


@task
def destroy_cluster(cluster):
    for app in cluster.app_set.all():
        app.destroy()
    cluster._scheduler.tearDown()


@task
def deploy_release(app, release):
    containers = app.container_set.all()
    # TODO: parallelize
    for c in containers:
        try:
            c.deploy(release)
        except Exception:
            c.state = 'error'
            c.save()
            raise


@task
def start_containers(containers):
    # TODO: parallelize
    for c in containers:
        try:
            c.create()
            c.start()
        except Exception:
            c.state = 'error'
            c.save()
            raise


@task
def stop_containers(containers):
    # TODO: parallelize
    for c in containers:
        try:
            c.destroy()
            c.delete()
        except Exception:
            c.state = 'error'
            c.save()
            raise


@task
def run_command(c, command):
    release = c.release
    version = release.version
    image = release.image
    try:
        # pull the image first
        rc, pull_output = c.run("docker pull {image}".format(**locals()))
        if rc != 0:
            raise EnvironmentError('Could not pull image: {pull_image}'.format(**locals()))
        # run the command
        docker_args = ' '.join(['-a', 'stdout', '-a', 'stderr', '--rm', image])
        env_args = ' '.join(["-e '{k}={v}'".format(**locals())
                             for k, v in release.config.values.items()])
        command = "docker run {env_args} {docker_args} {command}".format(**locals())
        return c.run(command)
    finally:
        c.delete()
