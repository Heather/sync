#!/usr/bin/env python

import os
import string
import time
from threading import Thread
from optparse import OptionParser

# Python 2x / 3x compatibility
try:  from configparser import ConfigParser 
except ImportError: 
    from ConfigParser import ConfigParser 
from subprocess import Popen, PIPE

#_____________________________________________________________________________________________

class VCS:
    git=0
    git_git=1
    git_mercurial=2
    git_subversion=3
    hg_hg=5

# misc global variables
sudo = False
fst = True

# statistics global variables
total = 0; success = 0; error = 0

#_____________________________________________________________________________________________
class shellrunner():
    def __init__(self, shell):
        self.shell = shell
    def command(self, x):
        return str(Popen(x.split(' ')
            , stdout    = PIPE
            , shell     = self.shell).communicate()[0])
    def sh(self, s):
        for s in (       self.command("sudo %s" % s) \
            if sudo else self.command(s)).split("\n"):
            if not s.startswith("b"): print(s)
#_____________________________________________________________________________________________
# Shell scripts

def gitSync(branch, upstream, upstreambranch, e):
    e.sh("git reset --hard")
    e.sh("git checkout %s" % branch)
    e.sh("git rebase --abort")
    e.sh("git pull origin %s" % branch)
    e.sh("git fetch %s %s" % (upstream, upstreambranch))
    e.sh("git pull --rebase %s %s" % (upstream, upstreambranch))
    e.sh("git push -f origin %s" % branch)

def gitPU(branch, e):
    e.sh("git pull origin %s" % branch)
    e.sh("git commit -am submodule")
    e.sh("git push -f origin %s" % branch)

def gitgitSync(e):
    e.sh("git pull origin master")
    e.sh("git fetch git master")
    e.sh("git push -f git master")

def githgSync(e):
    e.sh("hg pull")
    e.sh("hg update")
    e.sh("hg push git")

def hghgSync(branch, upstream, upstreambranch, e):
    e.sh("hg pull --update --rebase --branch %s %s" % (upstreambranch, upstream))
    e.sh("hg push %s --force" % branch)

def checkGitModifications(e):
    status = e.command("git status").split("\n")
    print("New: %s"         % [x[14:] for x in status if x.startswith("#\tnew file:   ")])
    print("Modified: %s"    % [x[14:] for x in status if x.startswith("#\tmodified:   ")])

#_____________________________________________________________________________________________
# Threads

class ParentUpdate(Thread):
    def __init__(self, vcs, branch, shell):
        Thread.__init__(self)
        self.vcs = vcs
        self.branch = branch
        self.e = shellrunner(shell)
    def run(self):
        if self.vcs == VCS.git:
            checkGitModifications(self.e)
            gitPU(self.branch, self.e)

class ThreadingSync(Thread):
    def __init__(self, vcs, branch, upstream, upstreambranch, shell):
        Thread.__init__(self)
        self.vcs = vcs
        self.branch = branch
        self.upstream = upstream
        self.upstreambranch = upstreambranch
        self.e = shellrunner(shell)
    def run(self):
        if self.vcs == VCS.git:
            checkGitModifications(self.e)
            gitSync(self.branch, self.upstream, self.upstreambranch, self.e)
        elif self.vcs == VCS.git_git:
            gitgitSync(self.e)
        elif self.vcs == VCS.git_mercurial:
            githgSync(self.e)
        elif self.vcs == VCS.git_subversion:
            print ("can't sync git from subversion yet")
        elif self.vcs == VCS.hg_hg:
            hghgSync(self.branch, self.upstream, self.upstreambranch, self.e)

#_____________________________________________________________________________________________

def DoUpdate(vcs, branch, useub, haveparent,upstream, upstreambranch, parent, shell):
    global success
    global error
    if not useub: upstreambranch = branch
    thrd = ThreadingSync(vcs, branch, upstream, upstreambranch, shell)
    thrd.setDaemon(True)
    thrd.start()

    failed = True # Because not success yet
    mustend = time.time() + 180
    while time.time() < mustend:
        if thrd.is_alive(): time.sleep(0.25)  
        else: 
            success+=1
            print(" --> successful synchronized :)")
            if haveparent:
                print(">>>>>>>>> Parent update: %s" % parent)
                os.chdir( parent.strip() )
                thrdp = ParentUpdate(vcs, branch, shell)
                thrdp.setDaemon(True)
                thrdp.start()
                succp = True
                mustendp = time.time() + 180
                while time.time() < mustendp:
                    if thrdp.is_alive(): time.sleep(0.25)  
                    else: 
                        print(" --> %s : successful synchronized :)" % parent)
                        succp = False
                        break
                if succp: print(" --> %s : timed out :(" % parent)
            failed = False
            break
    if failed: 
        error+=1
        print(" --> timed out :(")

#_____________________________________________________________________________________________

def SyncStarter(repo, shell):
    global fst
    global total
    global error
    
    vcs = VCS.git
    useub = False
    haveparent = False
    branches = ''
    branch = 'master'
    parent = ''
    upstreambranch = ''

    r = repo.split(" -t")
    rpth = ((r[0]).split(" "))
    pth  = rpth[0]

    print("------ Repository: %s ------" % pth)

    if len(r) > 1:
        svcs = ((r[1]).split(" "))[1]
        vcs = { 
            'git'       : VCS.git,
            'git git'   : VCS.git_git,
            'git hg'    : VCS.git_mercurial,
            'git svn'   : VCS.git_subversion,
            'hg hg'     : VCS.hg_hg}[svcs]

    t = repo.split(" -b")   # <----- Branch
    if len(t) > 1:
        branch = ((t[1]).split(" ")[1])
        branches = branch.split(",")
    pb = repo.split(" -u") # <----- Upstream Branch
    if len(pb) > 1:
        useub = True
        upstreambranch = ((pb[1]).split(" ")[1])
    sbm = repo.split(" -p") # <----- Submodule Parents
    if len(sbm) > 1:
        haveparent = True
        parent = ((sbm[1]).split(" ")[1])

    pdir = pth; upstream = 'upstream'
    if shell:
        if fst: fst = False
        else: os.chdir("..")
    if pth.startswith('git@'):
        if len(rpth) > 1:
            upstream = rpth[1]
            print(" --> upstream: %s" % upstream)
        else: 
            print(" --> %s : Failed to get upstream branch :(" % pth)
            return
        vcs = VCS.git
        if not shell:
            if not os.path.exists('/usr/share/sync/git'):
                os.makedirs('/usr/share/sync/git')
        gitp = (((r[0]).split("/"))[1].split("."))[0]
        pdir = { True: 'sync-%s'
               , False: '/usr/share/git/%s'} [shell] % gitp
        if not os.path.exists(pdir):
            e = shellrunner(shell)
            e.sh("git clone %s %s" % (pth, pdir))

    if os.path.exists(pdir):
        os.chdir(pdir)
        if len(branches) > 1:
            for b in branches:
                total += 1
                print("--> branch: %s" % b)
                DoUpdate(vcs, b, useub, haveparent, upstream, upstreambranch, parent, shell)
        else:
            total += 1
            DoUpdate(vcs, branch, useub, haveparent, upstream, upstreambranch, parent, shell)
    else: 
        error+=1
        print(" --> Failed, no such dir: %s :(" % pdir)
    print("______________________________________________________________________")

#_____________________________________________________________________________________________

def syncrepos(repos, shell): 
    for r in repos.split("\n"): 
        if r: SyncStarter(r, shell)
def syncgentoo(gentoo_x86):
    if os.path.exists(gentoo_x86):
        os.chdir(gentoo_x86)
        e = shellrunner(False)
        print( "##====---- pulling gentoo-x86 ----====##" )
        e.sh("cvs update")
        print( "##====---- regen cache for ::gentoo-x86 ----====##" )
        e.sh("egencache --update --repo=gentoo --portdir=%s --jobs=2" % gentoo_x86)
    else: print("wrong gentoo-x86 path: %s" % gentoo_x86)
#_____________________________________________________________________________________________
print("======================================================================")
print("         sync: Global repositories synchronizer v.4.0  ")
print("======================================================================")
#_____________________________________________________________________________________________
parser = OptionParser()
parser.add_option("-g", "--gentoo",
                  action="store_true", dest="gentoo", default=False,
                  help="only sync Genoo-xf86")
(options, args) = parser.parse_args()
config = ConfigParser()
try:
    if os.name == 'nt':     # -> Windows
        config.readfp(open('repolist.conf'))
        syncrepos( config.get('Repos','user') , True)
    else:                   # -> Unix systems
        config.readfp(open('/etc/repolist.conf'))
        if options.gentoo:  # -> Gentoo-x86:
            if os.geteuid() != 0: sudo = True
            gentoo_x86 = config.get('Gentoo', 'gentoo-x86')
            syncgentoo(gentoo_x86)
        else:               # -> Default
            if os.geteuid() == 0:
                print("warning: running from root, only root repositories is syncing")
            else:
                user = config.get('Repos','user')
                syncrepos(user, False)
                sudo = True
            # -> Root
            root = config.get('Repos','sudo')
            syncrepos(root, False)
except IOError: print('No repolist.conf found, check readme for example')
#_____________________________________________________________________________________________
print("  Statistics:  ")
print("----------------------------------------------------------------------")
print("      total : %d" % total)
print("      success : %d" % success)
print("      errors : %d" % error)
print("======================================================================")
#_____________________________________________________________________________________________
