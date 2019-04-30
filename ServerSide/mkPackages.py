#!/usr/bin/env python3

from __future__ import print_function
import os
import sys
from  ros4win_pkg import * 
import glob

if __name__ == '__main__':
  pkg=sys.argv[1]
  print("-- %s --" % pkg)
  pfiles=glob.glob("ros_pkg/%s/*.tgz" % pkg)

  data=[]

  for x in pfiles:
    data.append(get_pkg_data(x))
  fname="ros_pkg/%s/pkgs.yaml" %  pkg
  save_yaml(fname, data)


