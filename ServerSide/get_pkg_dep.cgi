#!/usr/bin/env python3

from __future__ import print_function
import cgi
import os
import cgitb
from ros4win_pkg import *

def cgi_main():
  cgitb.enable()

  if 'QUERY_STRING' in os.environ:
    query = cgi.parse_qs(os.environ['QUERY_STRING'])
  else:
    query = {}

  print("Content-Type: text/html;")
  print("")
  try:
    name=query['name'][0]
    res = get_dep_package(name)
    for x in res:
      print(x)
  except:
    print("")
 
def load_pkgs_yaml(name):
  fname="ros_pkg/%s/pkgs.yaml" % name
  data=load_yaml(fname)
  return data

def get_dep_package(mname):
  data=[]
  for nn in PKG_LIST:
    data += load_pkgs_yaml(nn)
  res=[]
  for x in data:
    if mname in x['depend']:
      res.append( x['package'] )
  return res

if __name__ == '__main__':
    cgi_main()
