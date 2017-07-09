#!/bin/bash

yum install -y emacs epel-release python-devel wget which java-1.8.0-openjdk libffi-devel openssl-devel
yum groupinstall -y "Development Tools"
yum install -y python-pip
pip install virtualenv
pip install --upgrade pip
