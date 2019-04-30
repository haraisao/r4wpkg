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

typ='name'
print("Content-Type: text/html;")
print("")
try:
  if 'type' in query:
    typ=query['type'][0]

  name=query['name'][0]

  if name == 'all':
    pkgs = ros4win_pkg.get_pkg_list_all()
    lpkg, llib = ros4win_pkg.get_dep_list(pkgs)
  elif ros4win_pkg.is_meta_package(name) or (":" in name):
    pkgs = ros4win_pkg.get_pkg_list_all2(1, name)
    lpkg, llib = ros4win_pkg.get_dep_list(pkgs)
  else:
    lpkg, llib = ros4win_pkg.get_dep_list(name)

  if typ == 'name':
    #lpkg.append(name)
    print(":".join(lpkg))
    print()
    print(":".join(llib))

  elif typ == 'json':
    print("{'pkg':'%s', 'lib':'%s'}" % (":".join(lpkg), ":".join(llib)))
  else:
    #print(ros4win_pkg.get_file_name_full(name))
    if lpkg:
      for p in lpkg:
        print(ros4win_pkg.get_file_name_full(p))
    else:
      print("")

except:
  print("")
  
