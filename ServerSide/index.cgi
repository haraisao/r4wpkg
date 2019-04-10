#!/usr/bin/env python3

from __future__ import print_function
import cgi
import os
import cgitb
import ros4win_pkg

cgitb.enable()

if 'QUERY_STRING' in os.environ:
    query = cgi.parse_qs(os.environ['QUERY_STRING'])
else:
    query = {}


print("Content-Type: text/html;")
print("")
try:
  cmd=query['cmd'][0]

  pkgs=[]
  libs=[]

  if cmd == 'run_dep' :
    name=query['name'][0]
    ros4win_pkg.get_run_dep_all(name, pkgs, libs)
    print ("Package:", pkgs)
    print("")
    print ("Libraries:", libs)
    print("")

  elif cmd == 'pkg_name':
    name=query['name'][0]
    val = ros4win_pkg.find_package(name)
    if val :
      print("%s/%s" % (val[0],  ros4win_pkg.get_file_name(val[1])))
  else:
    print("No such command:", cmd)
except:
  print("ERROR")
  
