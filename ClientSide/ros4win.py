#
#  Package manager for Ros4Win
#     Copyright(C) 2019 Isao Hara
import os
import sys
import requests
import hashlib
import sqlite3
from contextlib import closing
import datetime
import tarfile
import glob
import re
import traceback
import shutil
import signal

PKG_LIST=['ros_base', 'ros_desktop', 'control', 'plan', 'navigation', 'robot']
LIB_LIST=['local', 'setup']
PKG_BASE_DIR="ros_pkg/"
PKG_PREFIX="ros-melodic-"
PKG_EXT=".tgz"

PKG_MGR_DIR="/opt/_pkgmgr"
PKG_DB="ros4win.db"

PKG_REPO_BASE="http://hara.jpn.com/cgi/"

#######
# Remote
#
def get_pkg_hash_value(name):
  url="%spkg_hash.cgi?name=%s" % (PKG_REPO_BASE, name)
  res=requests.get(url)
  if res.status_code == 200:
    return res.text
  return ""

#
#
def get_package(fname, path=""):
  mon=['-', '\\', '|', '/']
  file_name=os.path.basename(fname)
  h_val=get_pkg_hash_value(file_name).strip()
  url="%spkg_get.cgi?name=%s" % (PKG_REPO_BASE, fname)
  res=requests.get(url, stream=True)

  if res.status_code == 200:
    if 'Content-Disposition' in res.headers:
      val=res.headers['Content-Disposition']
      if "attachment" in val and "filename=" in val:
        file_name=val.split('filename=')[-1]
    size=int(res.headers['Content-Length'])
    count = 1
    dl_chunk_size=1024
    bs=10
    if path :
      if not os.path.exists(path) :
        os.makedirs(path)
      file_name = path+"\\"+file_name
    #
    #  check file exists
    if os.path.exists(file_name):
      h_val2=get_hash_value(file_name).strip()
      if h_val == h_val2:
        print("Skip download:", fname)
        return
    #
    # save to file
    with open(file_name, 'wb') as f:
      for chunk in res.iter_content(chunk_size=dl_chunk_size):
        f.write(chunk)
        remain = (size - dl_chunk_size * count) / size
        n = int((1-remain)*bs)
        bar="=" * n + ">" + " " * (bs -n)
        print( "Download %s:|%s|(%d%%) %s\r" % (os.path.basename(file_name), bar, min(100- remain*100, 100), mon[count % 4]), end="")
        count += 1    
    print("")
  else:
    print("Fail to download: %s" % fname)
#
#
def get_pkg_dep(name, typ='json'):
    url="%spkg_dep.cgi?name=%s&type=%s" % (PKG_REPO_BASE, name, typ)
    res=requests.get(url)
    if res.status_code == 200:
        lst=res.text
        return lst
    return None
#
#
def get_pkg_list(pname):
    url="%spkg_list.cgi?name=%s" % (PKG_REPO_BASE, pname)
    res=requests.get(url)
    if res.status_code == 200:
        lst=eval(res.text)
        return lst
    return []

def get_pkgs_yaml(pname):
  url="%sget_pkg_dep.cgi?name=%s" % (PKG_REPO_BASE, pname)
  res=requests.get(url)
  if res.status_code == 200:
    lst=res.text.split()
    return lst
  return []

#######
#
#
def is_meta_pkg(name):
  return (name in PKG_LIST) or (name in LIB_LIST)

def exist_meta_pkg(names):
  for n in names:
    if is_meta_pkg(n) : return True
  return False

def get_hash_value(fname):
  if os.path.exists(fname):
    return hashlib.md5(open(fname, 'rb').read()).hexdigest()
  else:
    return None

def get_pkg_name(fname):
  name=os.path.basename(fname)
  if PKG_PREFIX in name:
    return name.replace(PKG_PREFIX, "").replace(PKG_EXT, "").replace("-", "_")
  else:
    return name.replace(PKG_EXT, "")

def split_drive_letter(fname):
  x=re.match(r'^[a-zA-Z]:', fname)
  if x : 
    sp=x.span()
    return (fname[sp[0]:sp[1]], fname[sp[1]:])
  return ["", fname]

def remove_pkg_file_all(pkg, drv):
  dbname="%s%s/%s" % (drv, PKG_MGR_DIR, PKG_DB)
  files=get_installed_files(pkg, dbname)

  if files:
    sfiles=sorted(files, key=len, reverse=True)
    for f in sfiles:
      fname="%s\\opt\\%s" % (drv, f)
      if os.path.exists(fname):
        if os.path.isfile(fname):
          os.remove(fname)
        else:
          try:
            os.removedirs(fname)
          except:
            pass
    delete_install_file_entries(pkg, dbname)
    delete_pkg_data(pkg, dbname)  
  return

def get_installed_pkgs(drv):
  return get_installed_packages("%s%s/%s" % (drv, PKG_MGR_DIR, PKG_DB))

####
# Download packages
#
def get_pkgs(names, path=""):
  for f in names:
    get_package(f, path)


#####
# Database
#
def create_db_table(name, schema, dbname=PKG_DB):
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    try:
      create_table = "create table %s (%s)" % (name, schema)
      c.execute(create_table)
      conn.commit()
    except:
      pass
    conn.close()

def exec_sql(sql, dbname=PKG_DB):
  res=[]
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    res=c.execute(sql).fetchall()
    conn.commit()
    conn.close()
  return res

def insert_pkg_data(name, fname, h_val=None, dbname=PKG_DB):
  create_db_table('packages', 'name text, fname text, run_dep text, lib_dep text, h_val text, uptime timestamp', dbname)

  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql="delete from packages where name='%s'" % name
    c.execute(sql)
    conn.commit()

    sql = "insert into packages (name, fname, h_val,run_dep,lib_dep,uptime) values (?,?,?,?,?,?)"
    ftime = datetime.datetime.fromtimestamp(os.stat(fname).st_mtime)
    res=get_pkg_dep(name).split("\n")
    h_val=get_hash_value(fname)
    data=(name, os.path.basename(fname), h_val, res[0], res[1], ftime)
    c.execute(sql, data)
    conn.commit()

    conn.close()

def get_pkg_data(name, dbname=PKG_DB):
  res=[]
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql = "select * from packages where name='%s'" % name
    res=c.execute(sql).fetchall()
    conn.commit()
    conn.close()
  return res

def get_installed_pkgs_list(dbname=PKG_DB):
  res=[]
  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql = "select * from packages"
    res1=c.execute(sql)
    res=res1.fetchall()
    conn.commit()
    conn.close()
  return res

def delete_pkg_data(name, dbname=PKG_DB):
  sql="delete from packages where name='%s'" % name
  try:
    res=exec_sql(sql, dbname)
    return True
  except:
    return False

def list_except(x, y, delim=";"):
  xx=x.split(delim)
  yy=y.split(delim)
  res=[]
  for v in xx:
    if not v in yy:
      res.append(v)
  return delim.join(res)

def register_info(dbname, pkgname, fname):
  create_db_table('install_info', "name text, path text, uptime timestamp", dbname)

  with closing(sqlite3.connect(dbname)) as conn:
    c = conn.cursor()
    sql = "insert into install_info (name, path, uptime) values (?,?,?)"
    ftime = datetime.datetime.now()
    data=(pkgname, fname, ftime)
    c.execute(sql, data)
    conn.commit()
    conn.close()


def get_installed_files(name, dbname):
  sql="select * from install_info where name='%s';" % name
  try:
    res=exec_sql(sql, dbname)
    return [x[1] for x in res]
  except:
    return []

def delete_install_file_entries(name, dbname):
  sql="delete from install_info where name='%s'" % name
  try:
    res=exec_sql(sql, dbname)
    return True
  except:
    return False

def get_installed_packages(dbname):
  sql="select distinct name from install_info;"
  try:
    res=exec_sql(sql, dbname)
    return [x[0] for x in res]
  except:
    return []

def check_installed_packages(name, dbname):
  sql="select distinct name from install_info where name='%s';" % name
  try:
    res=exec_sql(sql, dbname)
    return len(res)
  except:
    return 0

def get_dbname(to_dir, db):
  d, nm=split_drive_letter(to_dir)
  dbname = d+PKG_MGR_DIR+"/"+db
  return dbname

####
# Untar
# 
def untar(fname, to_dir, num=10, db=None):
  mon=['-', '\\', '|', '/']
  dbname=None
  signal.signal(signal.SIGINT, signal.SIG_DFL)
  try:
    arc=tarfile.open(fname)
    members=arc.getnames()
    if db:
      dbname=get_dbname(to_dir, db)
      if not os.path.exists(os.path.dirname(dbname)):
        os.makedirs(os.path.dirname(dbname))
      insert_pkg_data(get_pkg_name(fname), fname, None, dbname)
    n=len(members)
    x=n/num
    if x == 0 : x=1
    bar=">" + " " *num

    for i in range(n):
      try:
        arc.extract(members[i], path=to_dir)
        if db:
          register_info(dbname, get_pkg_name(fname), members[i])
      except:
        print("===Fail to extract===", members[i])
          
      bar = "=" * int(i/x) + ">" + " " * int((n-i)/x)
      s="Extract: %s |%s|(%d%%) %s     \r" % (os.path.basename(fname), bar, int(i*100/n), mon[i % 4])
      print(s, end="")
    print ("Extracted:",fname, "==>", to_dir, " " *(num+10))
    arc.close()
  except:
    print(fname,": Fail to extract...              ")
    traceback.print_exc()
    try:
      arc.close()
    except:
      pass

def ftopkg(name):
  fname=os.path.basename(name)
  return fname.replace(PKG_PREFIX, "").replace(".tgz", "").replace("-","_")

def check_pkg_installed(name, to_pkgdir):
  dbname=get_dbname(to_pkgdir, PKG_DB)
  return check_installed_packages(name, dbname)

def check_pkg_installed_old(name, to_pkgdir):
  ros_home = to_pkgdir+"\\ros\\melodic\\"
  share_dir1 = ros_home+"share\\"+name+"\\package.xml"
  share_dir2 = ros_home+"lib\\"+name.replace("lib", "")
  cmake_file1 = ros_home+"CMake\\%sConfig.cmake" % name
  cmake_file2 = ros_home+"CMake\\%s-config.cmake" % name
  return os.path.exists(share_dir1) or os.path.exists(share_dir2) or os.path.exists(cmake_file1) or os.path.exists(cmake_file2)

def install_pkg(path, dname, flag=False, verbose=False):
  f_list=glob.glob(path+"/*.tgz")
  to_libdir=dname+"\\local"
  to_pkgdir=dname+"\\opt"

  signal.signal(signal.SIGINT, signal.SIG_DFL)

  if not os.path.exists(to_libdir) :
    os.makedirs(to_libdir)
  if not os.path.exists(to_pkgdir) :
    os.makedirs(to_pkgdir)

  for fname in f_list:
    if PKG_PREFIX in fname:
      ff=ftopkg(fname)
      if flag or not check_pkg_installed(ff, to_pkgdir):
        untar(fname, to_pkgdir, 10, PKG_DB)
      else:
        if verbose:
          print("Skip install", ff)
    else:
      if "setup" in fname:
        if not os.path.exists(to_pkgdir+"\\start_ros.bat"):
          untar(fname, to_pkgdir)
      else:
        ff=os.path.basename(fname).replace(".tgz", "")
        if flag or not os.path.exists(to_libdir+"\\"+ff):
          untar(fname, to_libdir, 10, PKG_DB)
        else:
          if verbose :
            print("Skip install", ff)
#
#
def _main():
  path=""
  names=sys.argv[1].split(":")
  if len(sys.argv) > 2:
    path=sys.argv[2]
  
  for n in names:
    if is_meta_pkg(n):
      res=get_pkg_list(n)
      if res :
        get_pkgs(list(res.keys()), path)
    else:
      get_package(n, path)

#
#
if __name__ == '__main__':
  _main()