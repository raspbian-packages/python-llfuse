'''
xattr.pxd

This file contains Cython definitions for attr/xattr.h

Copyright © 2010 Nikolaus Rath <Nikolaus.org>

This file is part of Python-LLFUSE. This work may be distributed under
the terms of the GNU LGPL.
'''

IF TARGET_PLATFORM == 'darwin':
    cdef extern from "sys/xattr.h" nogil:
        int c_setxattr "setxattr" (char *path, char *name,
                                   void *value, int size,
                                   int flags, int options)

        int c_getxattr "getxattr" (char *path, char *name,
                                   void *value, int size,
                                   int position, int options)

        int XATTR_CREATE
        int XATTR_REPLACE
        int XATTR_NOFOLLOW
        int XATTR_NOSECURITY
        int XATTR_NODEFAULT

    cdef inline int setxattr (char *path, char *name,
                              void *value, int size, int flags) nogil:
        return c_setxattr(path, name, value, size, flags, 0)

    cdef inline int getxattr (char *path, char *name,
                              void *value, int size) nogil:
        return c_getxattr(path, name, value, size, 0, 0)

ELIF TARGET_PLATFORM == 'freebsd':
    cdef extern from "sys/types.h":
        pass

    cdef extern from "sys/extattr.h" nogil:

        int extattr_set_file(char *path, int attrnamespace,
                             char *attrname, void *data, int nbytes)
        int extattr_get_file(char *path, int attrnamespace,
                             char *attrname, void *data, int nbytes)

        int EXTATTR_NAMESPACE_USER
        int EXTATTR_NAMESPACE_SYSTEM

ELSE:
    cdef extern from "attr/xattr.h" nogil:
        int setxattr (char *path, char *name,
                      void *value, int size, int flags)

        int getxattr (char *path, char *name,
                      void *value, int size)

        int XATTR_CREATE
        int XATTR_REPLACE
