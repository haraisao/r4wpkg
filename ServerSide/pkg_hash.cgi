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
  name=query['name'][0]
  ros4win_pkg.print_hash_value(name)
except:
  print("ERROR")
  
