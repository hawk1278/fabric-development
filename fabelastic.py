#!/usr/bin/python
"""
Author: Rich O'Hara
Date: 26 May 2016
"""
from fabric.api import *
from fabric.colors import red, green, yellow

from fabric.contrib.console import confirm
from fabric.contrib.files import append
from fabtools.user import *
from fabtools.disk import mkfs, mount
from fabtools.require.files import directory
from fabtools.require import rpm
from fabtools.service import *
import os
import sys


env.roledefs = {
    "web-east":["192.168.1.46"]
}
groups= {
    "web":["webtest1","webtest2","webtest3"],
    "db":["db1","db2"],
    "developer":["dev1", "dev2", "dev3"]
}


@task
def setupsupervisor():
    require.python.package("supervisor")
    require.directory("/etc/supervisor.d", owner="", group="")
    require.file(path="/etc/supervisord.conf", source="/home/user/supervisord.conf", owner="", group="")  
    add_task("/usr/bin/supervisord -c /etc/supervisor.conf", "@reboot", "supervisor")


@task
def run_process(p):
    supervisor.start_process(p)


@task
def end_process(p):
    supervisor.stop_process(p)


@task
def add_user(user):
  create_user(user)

  
@task create_groups(*args):
    """
Creates groups
    """
  for arg in args:
    group.create(arg)


@task
def add_user_groups(user, group):
  modify(user, extra_groups=[group])

 
@task
def push_keys(user, keyfile):
    if exists(user):
        puts(green("Adding public key to {0} for user {1}.".format(env.host, user)))
        add_ssh_public_key(user, keyfile)


@task
def setpw(user):
  sudo('passwd {0}'.format(user))

 
@task
def install_pkgs(*args):
    for pkg in args:
        require.rpm.package(pkg, options="--quiet")


@task
def show_host():
    for host in env.hosts:
        puts(host)



