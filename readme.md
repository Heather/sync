Sync is util which will help you to keep your forks up to date!

[![Build Status](https://travis-ci.org/Heather/sync.png?branch=master)](https://travis-ci.org/Heather/sync)

all you need is: /etc/conf.d/repolist.conf or ../repolist.conf on windows

``` shell
[Repos]
user:
  nemerle -t git -b master,indent -u master
  /home/nen/contrib/haskell/hackport -t git
  /home/nen/contrib/haskell/hackport/cabal -p /home/nen/contrib/haskell/hackport

  /home/nen/contrib/mono/FAKE -t git -b develop
  git@github.com:Heather/gentoo-haskell.git git@github.com:gentoo-haskell/gentoo-haskell.git
sudo:
  /home/gentoo-haskell
```

(git and master branch are defaults)

and run forks-sync. [not that it can't setup repos for you yet]

``` python
def syncrepos(repos): 
    for r in repos.split("\n"): 
        if r: SyncStarter(r)

def sync(oz): 
    if oz == 'nt': 
        config.readfp(open('../repolist.conf'))
        syncrepos( config.get('Repos','user') )
    else: 
        config.readfp(open('/etc/conf.d/repolist.conf'))
        if os.geteuid() == 0:
            print("warning: running from root, only root repositories is syncing")
        else:
            user = config.get('Repos','user')
            syncrepos(user)
            sudo = True
        root = config.get('Repos','sudo')
        syncrepos(root)
```

it will be look alike that:

``` shell
=====================================================================================
                     sync: Global repositories synchronizer v.1.4  
=====================================================================================
------ Repository:  /home/nen/contrib/haskell/hackport ------
New: []
Modified: []
No rebase in progress?
From github.com:Heather/hackport
 * branch            master     -> FETCH_HEAD
From git://github.com/gentoo-haskell/hackport
 * branch            master     -> FETCH_HEAD
From git://github.com/gentoo-haskell/hackport
 * branch            master     -> FETCH_HEAD
Everything up-to-date
 -->  /home/nen/contrib/haskell/hackport : successful synchronized :)
______________________________________________________________________
------ Repository:  /home/nen/contrib/haskell/hackport/cabal ------
New: []
Modified: []
No rebase in progress?
From github.com:Heather/cabal
 * branch            master     -> FETCH_HEAD
From git://github.com/haskell/cabal
 * branch            master     -> FETCH_HEAD
From git://github.com/haskell/cabal
 * branch            master     -> FETCH_HEAD
Everything up-to-date
 -->  /home/nen/contrib/haskell/hackport/cabal : successful synchronized :)
>>>>>>>>> Parent update:  /home/nen/contrib/haskell/hackport
New: []
Modified: []
From github.com:Heather/hackport
 * branch            master     -> FETCH_HEAD
Everything up-to-date
 -->  /home/nen/contrib/haskell/hackport : successful synchronized :)
______________________________________________________________________
------ Repository:  /home/nen/contrib/mono/FAKE ------
New: []
Modified: []
No rebase in progress?
From github.com:Heather/FAKE
 * branch            develop    -> FETCH_HEAD
From git://github.com/fsharp/FAKE
 * branch            develop    -> FETCH_HEAD
From git://github.com/fsharp/FAKE
 * branch            develop    -> FETCH_HEAD
Everything up-to-date
 -->  /home/nen/contrib/mono/FAKE : successful synchronized :)
______________________________________________________________________
```

Installation
============

in gentoo you can install it from my overlay

``` shell
emerge sync
```

