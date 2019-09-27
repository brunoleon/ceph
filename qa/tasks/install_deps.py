"""
Task (and subtasks) for SES test automation

Linter:
    flake8 --max-line-length=100
"""
import logging

from scripts import Scripts

from teuthology.exceptions import (
    ConfigError,
    )
from teuthology.task import Task

log = logging.getLogger(__name__)


class InstallDeps(Task):

    def __init__(self, ctx, config):
        super(InstallDeps, self).__init__(ctx, config)
        self.log = log
        self.log.debug('self.ctx is {}'.format(ctx))
        # self.ctx.cluster.remotes looks like this:
        # [
        #    [
        #        Remote(name='ubuntu@target192168000016.teuthology'), 
        #        ['client.0']
        #    ]
        # ]
        #
        # We don't care how many names the remote has, nor do we care how many
        # remotes there are in the test. We just grab the first remote and
        # its first name.
        #
        self.log.debug("self.ctx.cluster.remotes is {}".format(self.ctx.cluster.remotes))
        #for remote, roles_list in self.ctx.cluster.remotes.iteritems():
        #    self.log.debug("remote object is {}".format(remote))
        #    self.log.debug("corresponding roles list is {}".format(roles_list))
        iterator = self.ctx.cluster.remotes.iteritems()
        (self.remote, roles_list) = iterator.next()
        self.log.debug("remote object is {}".format(self.remote))
        self.log.debug("corresponding roles list is {}".format(roles_list))
        self.ctx['remotes'] = {roles_list[0]: self.remote}
        self.scripts = Scripts(self.ctx, self.log)

    def setup(self):
        super(InstallDeps, self).setup()
        self.log.debug("Received config: ->{}<-".format(self.config))
        self.git_repo = 'https://github.com/ceph/ceph.git'
        if "repo" in self.config.keys():
            self.git_repo = 'https://github.com/{}/ceph.git'.format(self.config['repo'])
        self.git_branch = 'master'
        if "branch" in self.config.keys():
            self.git_branch = self.config['branch']

    def begin(self):
        """
        Clone ceph and run install-deps.sh. Display a diff from which it will be
        apparent which packages were installed by install-deps.sh when run on
        a pristine minimal OS install.

        Takes two config parameters, both optional, defaults shown:

        repo: ceph
              [will be inserted into string 'https://github.com/$REPO/ceph.git']
        branch: master
        """
        super(InstallDeps, self).begin()
        self.scripts.run(
            self.remote,
            'install-deps-test.sh',
            args=[self.git_repo, self.git_branch],
            as_root=False,
            )


    def end(self):
        super(InstallDeps, self).end()

    def teardown(self):
        super(InstallDeps, self).teardown()


task = InstallDeps
