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
    all_roles_of_type
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
        self.ssh_priv = 'tempkey.rsa'
        self.ssh_pub = 'tempkey.rsa.pub'
        self.set_agent = "eval `ssh-agent` && ssh-add ~/.ssh/%s && " % self.ssh_priv

    def __ssh_setup(self):
        log.debug("Executing SSH setup")
        self.__ssh_gen_key()
        self.__ssh_copy_priv()
        self.__ssh_copy_pub_to_caasp()

    def __ssh_gen_key(self):
        if os.path.isfile(self.ssh_priv):
            os.remove(self.ssh_priv)
        if os.path.isfile(self.ssh_pub):
            os.remove(self.ssh_pub)
        os.system('ssh-keygen -t rsa -b 2048 -P "" -f %s' % self.ssh_priv)
#            subprocess.check_output(['ssh-keygen', '-t', 'rsa', '-b', '2048', '-f', self.ssh_priv])
#            res = subprocess.check_output(["ls"])
#            log.debug(res)
#        except subprocess.CalledProcessError as e:
#            log.debug('error generating key')
#            log.debug(e.output)

    def __ssh_copy_priv(self):
        log.debug("Executing __ssh_copy_priv")
        try:
            subprocess.check_output(['scp', self.ssh_priv, '%s:.ssh/' %
                                     self.mgmt_remote])
        except subprocess.CalledProcessError as e:
            log.exception("Failed to copy private key to remote %s" % self.mgmt_remote)
            log.debug(e.output)

    def __ssh_copy_pub(self, remote):
        log.debug("Executing __ssh_copy_pub to %s" % remote.hostname)
        cmd = "ssh-copy-id -i %s %s" % (self.ssh_pub, remote)
        log.debug(cmd)
        os.system(cmd)
 #        try:
 #            subprocess.check_output(
 #                ['ssh-copy-id', '-i', self.ssh_pub, '%s' % remote])
 #        except subprocess.CalledProcessError as e:
 #            log.debug(e.output)

    def __ssh_copy_pub_to_caasp(self):
        for i in range(sum(1 for x in all_roles_of_type(
                self.ctx.cluster, 'caasp_master'))):
            remote = get_remote_for_role(
                self.ctx, "caasp_master." + str(i))
            self.__ssh_copy_pub(remote)
        for i in range(sum(1 for x in all_roles_of_type(
                self.ctx.cluster, 'caasp_worker'))):
            remote = get_remote_for_role(
                self.ctx, "caasp_worker." + str(i))
            self.__ssh_copy_pub(remote)

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
