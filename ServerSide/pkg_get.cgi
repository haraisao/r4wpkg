#!/usr/bin/env python3

from __future__ import print_function
import cgi
import os
import sys
import cgitb
import ros4win_pkg

cgitb.enable()
fname=None
if 'QUERY_STRING' in os.environ:
    query = cgi.parse_qs(os.environ['QUERY_STRING'])
else:
    query = {}

res=False

if 'name' in query:
  name=query['name'][0]

  fname=ros4win_pkg.get_file_name_full(name)

  res=ros4win_pkg.download_file(fname)

if not res:
  print("Content-Type: text/html")
  print()
  if fname:
    print("ERROR:", fname)
  else:
    print("ERROR")

