"""
Copyright (c) 2003-2005  Gustavo Niemeyer <gustavo@niemeyer.net>

This module offers extensions to the standard python 2.3+
datetime module.

This version of the code has been modified to remove the embedded copy
of zoneinfo-2008e.tar.gz and instead use the system data from the tzdata
package
"""
from dateutil.tz import tzfile
from tarfile import TarFile
import os

__author__ = "Gustavo Niemeyer <gustavo@niemeyer.net>"
__license__ = "PSF License"

__all__ = ["setcachesize", "gettz", "rebuild"]

def setcachesize(size):
    pass

def gettz(name):
    from dateutil.tz import gettz
    return gettz(name)

def rebuild(filename, tag=None, format="gz"):
    import tempfile, shutil
    tmpdir = tempfile.mkdtemp()
    zonedir = os.path.join(tmpdir, "zoneinfo")
    moduledir = os.path.dirname(__file__)
    if tag: tag = "-"+tag
    targetname = "zoneinfo%s.tar.%s" % (tag, format)
    try:
        tf = TarFile.open(filename)
        for name in tf.getnames():
            if not (name.endswith(".sh") or
                    name.endswith(".tab") or
                    name == "leapseconds"):
                tf.extract(name, tmpdir)
                filepath = os.path.join(tmpdir, name)
                os.system("zic -d %s %s" % (zonedir, filepath))
        tf.close()
        target = os.path.join(moduledir, targetname)
        for entry in os.listdir(moduledir):
            if entry.startswith("zoneinfo") and ".tar." in entry:
                os.unlink(os.path.join(moduledir, entry))
        tf = TarFile.open(target, "w:%s" % format)
        for entry in os.listdir(zonedir):
            entrypath = os.path.join(zonedir, entry)
            tf.add(entrypath, entry)
        tf.close()
    finally:
        shutil.rmtree(tmpdir)
