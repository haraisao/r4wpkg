#!/usr/bin/env python3
#
from __future__ import print_function
import tarfile
import os.path
import sys
import xml.dom.minidom
import glob
import hashlib
import sqlite3
from contextlib import closing
import datetime
import shutil


PKG_LIST=['ros_base', 'ros_desktop', 'control', 'plan', 'navigation', 'robot']
LIB_LIST=['local', 'setup']
PKG_BASE_DIR="ros_pkg/"
PKG_PREFIX="ros-melodic-"
PKG_EXT=".tgz"

PKG_DB="ros4win.db"

#
#
def merge_list(val, res):
  r=False
  try:
    for v in val:
      if not v in res:
        res.append(v)
        r=True
  except:
    pass
  return r
  
def tofname(name):
  return name.replace('_', '-')

def topname(name):
  return name.replace('-', '_')

def get_file_name(name):
  res=tofname(name)
  if not PKG_PREFIX in name:
    res=PKG_PREFIX+res
  if not PKG_EXT in name:
    res=res+PKG_EXT
  return res

def is_meta_pkg(name):
  return (name in PKG_LIST)
#
# Hash data
def print_hash_value(name):
  val=find_package(name)
  if val:
    fname=PKG_BASE_DIR+"%s/%s" % (val[0], get_file_name(val[1]))
    print(hashlib.md5(open(fname, 'rb').read()).hexdigest())
  else:
    fname=PKG_BASE_DIR+"local/%s.tgz" % (name)
    if os.path.exists(fname):
      print(hashlib.md5(open(fname, 'rb').read()).hexdigest())
    else:
      print("No such package")

def get_hash_value(fname):
    return hashlib.md5(open(fname, 'rb').read()).hexdigest()
#
# ROS package info
def get_pkg_info(lst):
  for v in lst:
    if 'package.xml' in v:
      return v

def get_package_xml(fname):
  arc=tarfile.open(fname)
  lst = arc.getnames()
  info = arc.extractfile(get_pkg_info(lst)).read()
  arc.close()
  return info.decode('utf-8')

def get_package_dom(fname):
  pkg_dom=dom=xml.dom.minidom.parseString(get_package_xml(fname))
  return pkg_dom

def get_depends(dom):
  deps =  dom.getElementsByTagName('run_depend')
  deps += dom.getElementsByTagName('exec_depend')
  deps += dom.getElementsByTagName('depend')
  res=[]
  for x in deps:
    try:
      res.append(x.childNodes[0].data)
    except:
      pass
  return res

def get_run_dep(name):
  arg=find_package(name)
  if not arg : return []
  (pkgname, name) = arg
  fname=PKG_BASE_DIR+"%s/%s" % (pkgname, get_file_name(name))
  dom=get_package_dom(fname)
  return get_depends(dom)

#
# 
def get_file_name_full(name):
  val=find_package(name)
  fname=None
  if val :
    fname=PKG_BASE_DIR+"%s/%s" % (val[0], get_file_name(val[1]))
  else:
    if 'setup' in name:
      fname=PKG_BASE_DIR+"setup/%s.tgz" % (name) 
    else:
      fname=PKG_BASE_DIR+"local/%s.tgz" % (name) 
  return  fname

def get_file_list(pkg):
  return glob.glob(PKG_BASE_DIR+"%s/*%s" % (pkg, PKG_EXT))

def file2pkg_name(fname, pkg):
    return fname.replace(PKG_BASE_DIR+"%s/" % pkg, "").replace(PKG_EXT, '')

def get_pkg_list(pkg):
  pkglist = pkg.split(":")

  for p in pkglist:
    files = get_file_list(p)
    for v in files:
      print( file2pkg_name(v,p), ":", get_hash_value(v))

def get_pkg_list_json(pkg):
  pkglist = pkg.split(":")
  res = []
  for p in pkglist:
    files =  get_file_list(p)
    for v in files:
      data="'%s':'%s'" % ( file2pkg_name(v, p), get_hash_value(v))
      res.append(data)
  result="{%s}" % (",".join(res))
  print(result)

def get_all_file(pkgs=PKG_LIST):
  res=[]
  for x in pkgs:
    flist=get_file_list(x)
    merge_list(flist, res)
  return res
    
def find_package(name, pkgs=PKG_LIST):
  #name=name.replace(PKG_PREFIX,"")
  fname=get_file_name(name)
  for x in pkgs:
    if os.path.exists(PKG_BASE_DIR+"%s/%s" % (x, fname)):
       return (x, name)
  return None

def get_run_dep_all(name, pkg_list, lib_list):
  lst = get_run_dep(name)
  if not lst : return pkg_list

  for p in lst:
    if not p in pkg_list:
      if find_package(p) :
        pkg_list.append(p)
        get_run_dep_all(p, pkg_list, lib_list)
      else:
        if not p in lib_list :
          lib_list.append(p)
  return pkg_list

def get_dep_list(arg=None):
  pkgs=[]
  libs=[]
  if arg is None:
    arg=sys.argv[1]
  get_run_dep_all(arg, pkgs, libs)
  
  return (pkgs, libs)
  
#
#  Database
#
def create_db_table(name, schema, dbname=PKG_DB):
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    try:
      create_table = "create table %s (%s)" % (name, schema)
      c.execute(create_table)
    except:
      pass
    conn.commit()

def init_pkg_db(dbname=PKG_DB):
   create_db_table('packages', 'name text, fname text, run_dep text, lib_dep text, h_val text, uptime timestamp', dbname)

def insert_pkg_data(name, fname=None, h_val=None, dbname=PKG_DB):
  if fname is None: fname=get_file_name_full(name)
  if fname is None : return

  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql = "insert into packages (name, fname, h_val,run_dep,lib_dep,uptime) values (?,?,?,?,?,?)" 
    ftime = datetime.datetime.fromtimestamp(os.stat(PKG_BASE_DIR+fname).st_mtime)
    pkg_list=[]
    lib_list=[]
    get_run_dep_all(name, pkg_list, lib_list)
    if not h_val:
      h_val=get_hash_value(PKG_BASE_DIR+fname)
    data=(name, fname, h_val, ';'.join(pkg_list), ';'.join(lib_list), ftime)
    c.execute(sql, data)
    conn.commit()

def get_pkg_data(name, dbname=PKG_DB):
  res=[]
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql = "select * from packages where name=%s" % name
    res=c.execute(sql).fetchall()
    conn.commit()
    conn.close()
  return res
 
#
# CGI
#
def download_file(fname):
  if os.path.isfile(fname):
    print("Content-Type: application/octet-stream")
    print("Content-Disposition: attachment; filename=%s" % os.path.basename(fname))
    print("Content-Length: %d" % os.path.getsize(fname))
    print()
    sys.stdout.flush()

    with open(fname,'rb') as f:
      shutil.copyfileobj(f, sys.stdout.buffer)
      sys.stdout.flush()
      f.close()
    return True
  else:
    return False

if __name__ == '__main__':
  pkgs, libs = get_dep_list()
  print ("Package:", pkgs)
  print ("Libraries:", libs)
  
