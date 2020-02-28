'''
Task that deploys a CAASP cluster on all the nodes
Linter:
    flake8 --max-line-length=100
'''
import logging
import os
import subprocess
from util import remote_exec
from teuthology.exceptions import ConfigError
from teuthology.misc import (
    delete_file,
    move_file,
    sh,
    sudo_write_file,
    write_file,
    copy_file,
    all_roles_of_type,
    append_lines_to_file,
    get_file
    )
from teuthology.orchestra import run
from teuthology.task import Task
from util import (
    get_remote_for_role,
    remote_exec
    )
log = logging.getLogger(__name__)


class Caasp(Task):
    """
    Deploy a Caasp cluster on all remotes using Skuba.
    Nodes are declared in suites/caasp folder
    """

    def __init__(self, ctx, config):
        super(Caasp, self).__init__(ctx, config)
        log.debug("beginning of constructor method")
        self.ctx['roles'] = self.ctx.config['roles']
        self.log = log
        self.remotes = self.cluster.remotes
        self.mgmt_remote = get_remote_for_role(self.ctx, "skuba_mgmt_host.0")
        self.ssh_priv = 'caasp_key.rsa'
        self.ssh_pub = 'caasp_key.rsa.pub'
        self.set_agent = "ssh-agent && ssh-add ~/%s && " % self.ssh_priv

    def __ssh_setup(self):
        """ Generate keys on management node. Copy pub to all of them. """
        log.debug("Executing SSH setup")
        self.__ssh_gen_key()
        self.__ssh_copy_pub_to_caasp()

    #def copy_file(from_remote, from_path, to_remote, to_path=None):

    def __ssh_gen_key(self):
        self.mgmt_remote.run(args=[
            'ssh-keygen',
            '-t',
            'rsa',
            '-b',
            '2048',
            '-P',
            '""',
            '-f',
            '{}'.format(self.ssh_priv),
        ])

    def __ssh_copy_pub_to_caasp(self):
        log.debug("Copying public key to remotes")
        data = get_file(self.mgmt_remote, self.ssh_pub)
        for i, _ in enumerate(all_roles_of_type(self.ctx.cluster, 'caasp_master')):
            r = get_remote_for_role(self.ctx, 'caasp_master.' + str(i))
            append_lines_to_file(r, '.ssh/authorized_keys', data)

    def __create_cluster(self):
        master_remote = get_remote_for_role(self.ctx, "caasp_master.0")
        commands = [
            "ssh-add -L",
            "skuba cluster init --control-plane {} cluster".format(master_remote.hostname),
            "cd cluster && skuba node bootstrap --user ubuntu --sudo --target {} my-master".format(
                master_remote.hostname),
        ]
        for command in commands:
            self.mgmt_remote.sh("%s %s" % (self.set_agent, command))
        for i in range(sum(1 for x in all_roles_of_type(
                self.ctx.cluster, 'caasp_worker'))):
            worker_remote = get_remote_for_role(
                self.ctx, "caasp_worker." + str(i))
            command = "cd cluster;skuba node join --role worker --user ubuntu --sudo --target {} worker.{}".format(
                worker_remote.hostname, str(i))
            self.mgmt_remote.sh("%s %s" % (self.set_agent, command))

    def begin(self):
        self.__ssh_setup()
        self.__create_cluster()

    def end(self):
        pass

    def teardown(self):
        pass


task = Caasp
