#!/bin/bash
#set -e

if [ ! -d  venv ] ; then
  virtualenv venv -p /usr/bin/python2
fi

source venv/bin/activate
pip install -r requirements.txt
pip install -e .
