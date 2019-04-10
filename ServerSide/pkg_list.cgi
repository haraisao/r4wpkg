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

typ='json'
print("Content-Type: text/html;")
print("")
try:
  if 'type' in query:
    typ=query['type'][0]
  name=query['name'][0]
  if typ == 'json':
    ros4win_pkg.get_pkg_list_json(name)
  else:
    ros4win_pkg.get_pkg_list(name)
except:
  print("ERROR")
  
