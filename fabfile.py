#!/usr/bin/python
"""
Author: Rich O'Hara
Date: 26 May 2016
Description:
Sample Fabric fabfile demonstrating the use of Fabric, Cuisine, and FabTools.  I really appreciate all the hard work that the authors and contributors have put in to these libraries!  Thank you!
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
from cuisine import *
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
def add_user(user):
    puts(green("Creating user: {0}".format(user)))
    user_create(user)
    sudo("passwd {0}".format(user))


@task
def add_groups(*args):
    for group in args:
        puts(green("Adding group: {0}".format(value)))
        group_ensure(value)
  
 
@task
def push_keys(user, keyfile):
    puts(green("Adding public key to {0} for user {1}.".format(env.host, user)))
    add_ssh_public_key(user, keyfile)

 
@task
def install_pkgs(*args):
    for pkg in args:
        require.rpm.package(pkg, optoins="--quiet")


@task
def fail_task(device="sdc;"):
    disk_list = device.split(";")
    print disk_list


@task
def configure_disks(*args):
         puts(green("Preparring disk for use."))
         for disk in args:
             with settings(warn_only=True): 
                 puts(green("Setting label to 'msdos'."))
                 result = sudo("/sbin/parted -s /dev/{0} mklabel msdos".format(disk))
                 if result.failed and not confirm("parted failed to mklabel.  Continue?"):
                     abort("Aborting task")
                 puts(green("Partitioning disk."))
                 result = sudo("/sbin/parted -s /dev/{0} mkpart primary 0% 100%".format(disk))
                 if result.failed and not confirm("parted failed to create partition.  Continue?"):
                     abort("Aborting task")
                 result = sudo("/sbin/parted -s /dev/{0} set 1 lvm on".format(disk))
                 if result.failed and not confirm("parted failed to set lvm tag on partition.  Continue?"):
                     abort("Aborting task")

@task
def create_vg(vgrp="datavg01", *args):
    with settings(warn_only=True):
        result = sudo("/sbin/vgcreate {0} {1}".format(vgrp, ' '.join(args)))
        if result.failed:
            puts(red("Failed to create volume group, {0}.".format(vgrp)))

        
@task
def create_vol(vgrp="datavg01", vol_name="datavol01"):
    with settings(warn_only=True):
        result = sudo("/sbin/lvcreate -n {0} -l 100%FREE {1}".format(vol_name, vgrp))
        if result.failed:
            puts(red("Failed to create logical volume.")) 
        
@task
def format_vol(device="/dev/datavg01/datavol01", fstype="ext4"):
    mkfs(device, fstype)

    
@task
def mount_device(device="/dev/datavg01/datavol01", mountpoint="/data/brick1", fstype="ext4"):
    directory(mountpoint, use_sudo=True)
    append("/etc/fstab", "{0}    {1}    {2}    defaults,nosuid,nodev    1 2".format(device, mountpoint, fstype), use_sudo=True)
    mount(device, mountpoint)
    sudo("mount")


@task
def start(svc):
    require.service.started(svc)


@task
def stop(svc):
    require.service.stopped(svc)


@task
def reload(svc):
    service.reload(svc)

@task 
def add_repo(**kwargs):
    env.reponame = kwargs["reponame"]
    env.repotitle = kwargs["repotitle"]
    env.repourl = kwargs["repourl"]'https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.2/x86_64/'
    source = os.path.join(fabdir,'templates/mongodb.repo')
    upload_template(source,'/etc/yum.repos.d/mongodb.repo',context=dict(env), mode=0700, use_sudo=True)


@task
def init_rs():
    put('initreplica.js', '/home/rohara/initrepl.js', use_sudo=True)
    sudo('mongo {0}:27017 /home/rohara/initreplica.js'.format(env.host), shell=True)


@task
def show_host():
    for host in env.hosts:
        puts(host)


@task
def setupsupervisor()
    require.python.package("supervisor")
    require.directory("/etc/supervisor.d", owner="", group="")
    require.file(path="/etc/supervisord.conf", source="/local/path/supervisord.conf", owner="", group="")
    add_task("/usr/bin/supervisord -c /etc/supervisord.conf","@reboot","supervisor")

@task
def run_process(p):
    supervisor.start_process(p)


@task
def end_process(p):
    supervisor.stop_process(p)

@task
def add_user(user):
    create(user)



