import re
import github

repositories = {}

class Repository(object):

    stepClass = None

    def __init__(self, url, properties=None):
        self.url = url
        self.properties = properties or {}
        repositories[url] = self

    def set_properties(self, include, exclude):
        for p in include:
            if p in self.properties:
                if not self.properties[p]:
                    raise ValueError, \
                        'property %s was already excluded from repository %s: %s' % (
                        p,self.url, self.properties)
            else:
                self.properties[p] = True

        for p in exclude:
            if p in self.properties:
                if self.properties[p]:
                    raise ValueError, \
                        'property %s was already included in repository %s: %s' % (
                        p,self.url, self.properties)
            else:
                self.properties[p] = False

    def match_url(self, url):
        """Used for change filtering; True iff url identifies the same repository."""
        return self.url == url

    def steps(self, *args, **kw):
        return [ self.stepClass(repourl = self.url, *args, **kw) ]


import buildbot.steps.source

class Git(Repository):
    """
    A repository whose steps use Git, but unlike BuildBot, *do*
    consider submodules by default.  Seriously, who wants to ignore
    submodules?
    """
    stepClass = buildbot.steps.source.Git

    def steps(self, *args, **kw):
        kw.setdefault('submodules', True)
        return self.buildbot_issue_2002_workaround(*args,**kw) + super(Git,self).steps(*args, **kw)
        

    def buildbot_issue_2002_workaround(self, *args, **kw):
        from buildbot.steps.shell import ShellCommand
        return [
            ShellCommand(
                name='BuildBot Ticket #2002 Workaround Step 1',
                command='mkdir %s && rmdir %s && git clone %s' % (self.name,self.name,self.url),
                flunkOnFailure=False,
                haltOnFailure=False,
                description='cloning',
                descriptionDone='cloned'),
            ShellCommand(
                name='BuildBot Ticket #2002 Workaround Step 2',
                command= ['git', 'fetch', self.url],
                flunkOnFailure=True,
                haltOnFailure=True,
                workdir=self.name,
                description='fetching',
                descriptionDone='fetched') ]
                
    @property
    def name(self):
        """
        The name of the repository: the last element of the url, sans .git extension if any
        """
        return re.match('.*/(.*?)(?:.git)?$', self.url).group(1)

class GitHub(Git):
    protocols=dict(
        git='git://github.com/%s',
        http='http://github.com/%s',
        https='https://github.com/%s',
        ssh='git@github.com:%s',
        )

    def __init__(self, id, protocol='http'):
        
        super(GitHub,self).__init__(GitHub.protocols[protocol] % id)
        self.id = id
        self.protocol = protocol

    def __repr__(self):
        return self.__class__.__module__ + '.' + self.__class__.__name__+repr((self.id,self.protocol))

    def match_url(self, url):
        from twisted.python import log
        m = github.url_pattern.match(url)
        log.msg('GitHub(%r) matching %r against %r...' % (self.url, m and m.group(1), self.id))
        ret = m.group(1) == self.id
        log.msg('...%s' % ret)
        return ret
