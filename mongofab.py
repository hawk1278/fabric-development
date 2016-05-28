#!/usr/bin/python
import os
from fabric.api import *
from fabric.contrib.files import upload_template
from fabtools.require import service
from fabtools import rpm

fabdir = '/Users/rohara/development/fab-dev'

def copy_mongo_configs(bindip, bindport, replset):
    env.bindip = bindip
    env.bindport = bindport
    env.replset = replset
    source = os.path.join(fabdir,'templates/mongod.conf')
    upload_template(source,'/etc/mongod.conf', context=dict(env), mode=0764, use_sudo=True)
    sudo('chown mongod:root /etc/mongod.conf', shell=True)


@task
def init_rs():
    put('initreplica.js', '/home/rohara/initrepl.js', use_sudo=True)
    sudo('mongo {0}:27017 /home/rohara/initreplica.js'.format(env.host), shell=True)


@task
def start_mongo(svc='mongod'):
    sudo('service {0} start'.format(svc), shell=True)


@task
def stop_service(svc='mongod'):
    sudo('service {0} stop', shell=True)


@task
def enable_service(svc='mongod'):
    sudo('chkconfig {0} on'.format(svc), shell=True)


@task
def disable_service(svc='mongod'):
    sudo('chkconfig {0} off'.format(svc), shell=True)


def add_mongo_repo():
    env.reponame = 'MongoDB Repository'
    env.repotitle = 'MongoDB'
    env.repourl = 'https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/3.2/x86_64/'
    source = os.path.join(fabdir,'templates/mongodb.repo')
    upload_template(source,'/etc/yum.repos.d/mongodb.repo',context=dict(env), mode=0700, use_sudo=True)


@task
def deploy_mongo(bindip, bindport, replset):
    add_mongo_repo()
    sudo('yum install -y mongodb-org, mongodb-org-mongos, mongodb-org-server, mongodb-org-shell, mongodb-org-tools', shell=True)
    copy_mongo_configs(bindip, bindport, replset)
    enable_service()
    start_mongo()
    init_rs()
