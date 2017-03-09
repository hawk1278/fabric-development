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
import boto3 
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

# User tasks
@task
def add_user(user):
    """
    fab -R <role>/-H <host ip or name> add_user:username
    """
    puts(green("Creating user: {0}".format(user)))
    user_create(user)
    sudo("passwd {0}".format(user))

@task
def add_groups(*args):
    """
    fab -R <role>/-H <host ip or name> add_groups:group1,group2
    """
    for group in args:
        puts(green("Adding group: {0}".format(value)))
        group_ensure(value)
  
@task
def add_user_groups(user,group):
    """
    Add additional groups to a user.
    fab -R <role>/-H <host ip or name> add_user_groups:username,group
    """
    modify(user, extra_groups=[group])

@task
def push_keys(user, keyfile):
    """
    Push a users public key to a host.
    fab -R <role>/-H <host ip or name> push_keys:username,/path/to/keyfile
    """
    puts(green("Adding public key to {0} for user {1}.".format(env.host, user)))
    add_ssh_public_key(user, keyfile)


@task
def enable_sudoer(user):
    """
    Add user to sudoers.d.
    fab -R <role>/-H <host ip or name> enable_sudoer:username
    """
    source = "templates/sudoers"
    env.u = u
    upload_template(source,"/etc/sudoers.d/{0}".format(u),context=dict(env), mode=0640, use_sudo=True)
    with cd("/etc/sudoers.d"):
        sudo("chown -R root:root *")
   
@task
def setpw(user):
    sudo('passwd {0}'.format(user))


# Package and yum repo tasks
@task
def install_pkgs(*args):
    """
    Install a comma separated list of packages.
    fab -R <role>/-H <host ip or name> install_pkgs:pkg1,pkg2,pkg3
    """
    for pkg in args:
        require.rpm.package(pkg, optoins="--quiet")

@task 
def add_repo(**kwargs):
    env.reponame = kwargs["reponame"]
    env.repotitle = kwargs["repotitle"]
    env.repourl = kwargs["repourl"]
    source = os.path.join(fabdir,'templates/yum.repo')
    upload_template(source,'/etc/yum.repos.d/{0}.repo'.format(kwargs["reponame"]), context=dict(env), mode=0700, use_sudo=True)

@task
def fail_task(device="sdc;"):
    disk_list = device.split(";")
    print disk_list

# Disk and LVM tasks
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
def init_rs():
    put('initreplica.js', '/home/rohara/initrepl.js', use_sudo=True)
    sudo('mongo {0}:27017 /home/rohara/initreplica.js'.format(env.host), shell=True)


@task
def show_host():
    for host in env.hosts:
        puts(host)

# Service tasks
@task
def start(svc):
    require.service.started(svc)

@task
def stop(svc):
    require.service.stopped(svc)

@task
def reload(svc):
    service.reload(svc)

# Supervisor tasks
@task
def setupsupervisor():
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

# Application deployment tasks
@task
def deploy_config(local_config_dir, config_dir, config):
  """
  Part of REST API deployment to upload specific supervisor configs
  """
  if exists("{0}/{1}".format(config_dir, config)) is False:
     with lcd(local_config_dir):
       with cd(config_dir):
          put("./{0}".format(config), "./{0}".format(config), use_sudo=True)
          supervisor.reload()

@task 
def clone_repo():
    """
    Part of REST API deployment to clone repos.
    clone git repo with fabric/fab_tools
    """
    with cd(app_dir):
        run('git clone -b develop {0} {1}'.format(gitrepo, now))


def create_link():
  """
  Part of API deployment to create a symbolic like called current to most recent releast
  """
  if is_link('current'):
    sudo("rm -f current")
    run("ln -s {0} current".format(now))
  else:
    run("ls -s {0} current".format(now))


