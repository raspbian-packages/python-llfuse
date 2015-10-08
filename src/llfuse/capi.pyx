'''
capi.pxy

Copyright © 2013 Nikolaus Rath <Nikolaus.org>

This file is part of Python-LLFUSE. This work may be distributed under
the terms of the GNU LGPL.
'''

# Version is defined in setup.py
cdef extern from *:
    char* LLFUSE_VERSION
__version__ = LLFUSE_VERSION.decode('utf-8')


###########
# C IMPORTS
###########

from fuse_lowlevel cimport *
from libc.sys.stat cimport stat as c_stat, S_IFMT, S_IFDIR
from libc.sys.types cimport mode_t, dev_t, off_t
from libc.stdint cimport uint32_t
from libc.stdlib cimport const_char
from libc cimport stdlib, string, errno, dirent, xattr
from posix.unistd cimport getpid
from posix.time cimport clock_gettime, CLOCK_REALTIME, timespec
from cpython.bytes cimport (PyBytes_AsStringAndSize, PyBytes_FromStringAndSize,
                            PyBytes_AsString, PyBytes_FromString)
cimport cpython.exc
from cpython.version cimport PY_MAJOR_VERSION


######################
# EXTERNAL DEFINITIONS
######################

cdef extern from "signal.h" nogil:
    int kill(pid_t pid, int sig)
    enum: SIGTERM

# Include components written in plain C
cdef extern from "lock.c" nogil:
    int acquire(double timeout) nogil
    int release() nogil
    int c_yield(int count) nogil
    int init_lock() nogil
    int EINVAL
    int EDEADLK
    int EPERM
    int EPROTO
    int ETIMEDOUT
    int ENOMSG

cdef extern from "time.c" nogil:
    long GET_ATIME_NS(c_stat* buf)
    long GET_CTIME_NS(c_stat* buf)
    long GET_MTIME_NS(c_stat* buf)

    void SET_ATIME_NS(c_stat* buf, long val)
    void SET_CTIME_NS(c_stat* buf, long val)
    void SET_MTIME_NS(c_stat* buf, long val)

cdef extern from "Python.h" nogil:
    void PyEval_InitThreads()

cdef extern from "version.c":
    pass

################
# PYTHON IMPORTS
################

import os
import logging
import sys
import os.path
import threading
from llfuse.pyapi import FUSEError, strerror, Operations, RequestContext, EntryAttributes
from collections import namedtuple

if PY_MAJOR_VERSION < 3:
    from Queue import Queue
    str_t = bytes
else:
    from queue import Queue
    str_t = str

##################
# GLOBAL VARIABLES
##################

log = logging.getLogger("llfuse")
fse = sys.getfilesystemencoding()

cdef object operations
cdef object mountpoint_b
cdef fuse_session* session = NULL
cdef fuse_chan* channel = NULL
cdef fuse_lowlevel_ops fuse_ops
cdef object exc_info

init_lock()
lock = Lock.__new__(Lock)
lock_released = NoLockManager.__new__(NoLockManager)

_notify_queue = Queue(maxsize=1000)
inval_inode_req = namedtuple('inval_inode_req', [ 'inode', 'attr_only' ])
inval_entry_req = namedtuple('inval_entry_req', [ 'inode_p', 'name' ])

# Exported for access from Python code
ROOT_INODE = FUSE_ROOT_ID
ENOATTR = errno.ENOATTR

#######################
# FUSE REQUEST HANDLERS
#######################

include "handlers.pxi"

####################
# INTERNAL FUNCTIONS
####################

include "misc.pxi"

####################
# FUSE API FUNCTIONS
####################

include "fuse_api.pxi"
