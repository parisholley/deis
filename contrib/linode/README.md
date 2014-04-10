How to configure Deis on Linode
===================================================

Before choosing Linode as your provider to run Deis, please be aware of the following:

* Because Linode does not have a concept of "images" (like on Digital Ocean), we provision servers from scratch each time. This saves the cost of keeping a contoller and node instance running ($20 each), at the expense of a long provisioning cycle.
* Linode charges up-front for all provisioned servers, however will credit your account if you decided to destroy the servers.
* The linode kernel does not support "Cgroup memory controller" so you will not be able to set memory limits on your docker containers.

Here are the steps to get started on Linode:

* install [linode-cli][lcli] (make sure to do the initial configuration)
* execute provision-controller.sh

[lcli]: https://github.com/linode/cli
