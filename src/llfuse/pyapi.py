# -*- coding: utf-8 -*-
'''
pyapi.py

Copyright © 2013 Nikolaus Rath <Nikolaus.org>

This file is part of Python-LLFUSE. This work may be distributed under
the terms of the GNU LGPL.
'''

from __future__ import division, print_function, absolute_import

import os
import errno
import logging
import stat

log = logging.getLogger('llfuse')

def strerror(errno):
    try:
        return os.strerror(errno)
    except ValueError:
        return 'errno: %d' % errno

class RequestContext:
    '''
    Instances of this class are passed to some `Operations` methods to
    provide information about the caller of the syscall that initiated
    the request.
    '''

    __slots__ = [ 'uid', 'pid', 'gid', 'umask' ]

    def __init__(self):
        for name in self.__slots__:
            setattr(self, name, None)

class EntryAttributes:
    '''
    Instances of this class store attributes of directory entries.
    Most of the attributes correspond to the elements of the ``stat``
    C struct as returned by e.g. ``fstat`` and should be
    self-explanatory.

    The access, modification and creation times may be specified
    either in nanoseconds (via the *st_Xtime_ns* attributes) or in
    seconds (via the *st_Xtime* attributes). When times are specified
    both in seconds and nanoseconds, the nanosecond representation
    takes precedence. If times are represented in seconds, floating
    point numbers may be used to achieve sub-second
    resolution. Nanosecond time stamps must be integers. Note that
    using integer nanoseconds is more accurately than using float
    seconds.

    Request handlers do not need to return objects that inherit from
    `EntryAttributes` directly as long as they provide the required
    attributes.
    '''

    # Attributes are documented in rst/data.rst

    __slots__ = [ 'st_ino', 'generation', 'entry_timeout',
                  'attr_timeout', 'st_mode', 'st_nlink', 'st_uid', 'st_gid',
                  'st_rdev', 'st_size', 'st_blksize', 'st_blocks',
                  'st_atime', 'st_atime_ns', 'st_mtime', 'st_mtime_ns',
                  'st_ctime', 'st_ctime_ns' ]

    def __init__(self):
        self.st_ino = None
        self.generation = 0
        self.entry_timeout = 300
        self.attr_timeout = 300
        self.st_mode = stat.S_IFREG
        self.st_nlink = 1
        self.st_uid = 0
        self.st_gid = 0
        self.st_rdev = 0
        self.st_size = 0
        self.st_blksize = 4096
        self.st_blocks = 0
        self.st_atime = 0
        self.st_mtime = 0
        self.st_ctime = 0
        self.st_atime_ns = None
        self.st_mtime_ns = None
        self.st_ctime_ns = None

class StatvfsData:
    '''
    Instances of this class store information about the file system.
    The attributes correspond to the elements of the ``statvfs``
    struct, see :manpage:`statvfs(2)` for details.

    Request handlers do not need to return objects that inherit from
    `StatvfsData` directly as long as they provide the required
    attributes.
    '''

    # Attributes are documented in rst/operations.rst

    __slots__ = [ 'f_bsize', 'f_frsize', 'f_blocks', 'f_bfree',
                  'f_bavail', 'f_files', 'f_ffree', 'f_favail' ]

    def __init__(self):
        for name in self.__slots__:
            setattr(self, name, None)

class FUSEError(Exception):
    '''
    This exception may be raised by request handlers to indicate that
    the requested operation could not be carried out. The system call
    that resulted in the request (if any) will then fail with error
    code *errno_*.
    '''

    __slots__ = [ 'errno' ]

    def __init__(self, errno_):
        super(FUSEError, self).__init__()
        self.errno = errno_

    def __str__(self):
        return strerror(self.errno)

class Operations(object):
    '''
    This class defines the general and request handler methods that an
    Python-LLFUSE file system may implement. If a particular request handler has
    not been implemented, it must raise `FUSEError` with an errorcode of
    `errno.ENOSYS`. Further requests of this type will then be handled directly
    by the FUSE kernel module without calling the handler again.

    It is recommended that file systems are derived from this class
    and only overwrite the handlers that they actually implement. (The
    default implementations defined in this class all just raise the
    not-implemented exception).

    The only exception that request handlers are allowed to raise is
    `FUSEError`. This will cause the specified errno to be
    returned by the syscall that is being handled.

    Note that all character data (directory entry names, extended
    attribute names and values, symbolic link targets etc) are passed
    as `bytes` and must be returned as `bytes`. This applies to both
    running under Python 2.x and 3.x
    '''

    def init(self):
        '''Initialize operations

        This function will be called just before the file system
        starts handling requests. It must not raise any exceptions
        (including `FUSEError`, since this method is not handling a
        particular syscall).
        '''

        pass

    def destroy(self):
        '''Clean up operations.

        This method will be called when `llfuse.close` has been called
        and the file system is about to be unmounted.

        Since this handler is thus *not* run as part of the main loop,
        it is also *not* called with the global lock acquired (unless
        the caller of `llfuse.close` already holds the lock).

        This method must not raise any exceptions (including
        `FUSEError`, since this method is not handling a particular
        syscall).
        '''

        pass

    def lookup(self, parent_inode, name):
        '''Look up a directory entry by name and get its attributes.

        If the entry *name* does not exist in the directory with inode
        *parent_inode*, this method must raise `FUSEError` with an
        errno of `errno.ENOENT`. Otherwise it must return an
        `EntryAttributes` instance.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.

        The file system must be able to handle lookups for :file:`.`
        and :file:`..`, no matter if these entries are returned by
        `readdir` or not.
        '''

        raise FUSEError(errno.ENOSYS)

    def forget(self, inode_list):
        '''Notify about inodes being removed from the kernel cache

        *inode_list* is a list of ``(inode, nlookup)`` tuples. This
        method is called when the kernel removes the listed inodes
        from its internal caches. *nlookup* is the number of times
        that the inode has been looked up by calling either of the
        `lookup`, `create`, `symlink`, `mknod`, `link` or `mkdir`
        methods.

        The file system is expected to keep track of the number of
        times an inode has been looked up and forgotten. No request
        handlers other than `lookup` will be called for an inode with
        a lookup count of zero.

        If the lookup count reaches zero after a call to `forget`, the
        file system is expected to check if there are still directory
        entries referring to this inode and, if not, delete the inode
        itself.

        If the file system is unmounted, it will may not receive
        `forget` calls for inodes that are still cached. The `destroy`
        method may be used to clean up any remaining inodes for which
        no `forget` call has been received.
        '''

        pass

    def getattr(self, inode):
        '''Get attributes for *inode*

        This method should return an `EntryAttributes` instance with
        the attributes of *inode*. The
        `~EntryAttributes.entry_timeout` attribute is ignored in this
        context.
        '''

        raise FUSEError(errno.ENOSYS)


    def setattr(self, inode, attr):
        '''Change attributes of *inode*

        *attr* is an `EntryAttributes` instance with the new
        attributes. Only the attributes `~EntryAttributes.st_size`,
        `~EntryAttributes.st_mode`, `~EntryAttributes.st_uid`,
        `~EntryAttributes.st_gid`, `~EntryAttributes.st_atime` and
        `~EntryAttributes.st_mtime` are relevant. Unchanged attributes
        will have a value `None`.

        The method should return a new `EntryAttributes` instance
        with the updated attributes (i.e., all attributes except for
        `~EntryAttributes.entry_timeout` should be set).
        '''

        raise FUSEError(errno.ENOSYS)

    def readlink(self, inode):
        '''Return target of symbolic link

        The return value must have type `bytes`.
        '''

        raise FUSEError(errno.ENOSYS)


    def mknod(self, parent_inode, name, mode, rdev, ctx):
        '''Create (possibly special) file

        *ctx* will be a `RequestContext` instance. The method must
        return an `EntryAttributes` instance with the attributes of
        the newly created directory entry.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def mkdir(self, parent_inode, name, mode, ctx):
        '''Create a directory

        *ctx* will be a `RequestContext` instance. The method must
        return an `EntryAttributes` instance with the attributes of
        the newly created directory entry.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def unlink(self, parent_inode, name):
        '''Remove a (possibly special) file

        If the file system has received a `lookup`, but no `forget`
        call for this file yet, `unlink` is expected to remove only
        the directory entry and defer removal of the inode with the
        actual file contents and metadata until the `forget` call is
        received.

        Note that an unlinked file may also appear again if it gets a
        new directory entry by the `link` method.
        '''

        raise FUSEError(errno.ENOSYS)

    def rmdir(self, inode_parent, name):
        '''Remove a directory

        If the file system has received a `lookup`, but no `forget`
        call for this file yet, `unlink` is expected to remove only
        the directory entry and defer removal of the inode with the
        actual file contents and metadata until the `forget` call is
        received.
        '''

        raise FUSEError(errno.ENOSYS)

    def symlink(self, inode_parent, name, target, ctx):
        '''Create a symbolic link

        *ctx* will be a `RequestContext` instance. The method must
        return an `EntryAttributes` instance with the attributes of
        the newly created directory entry.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def rename(self, inode_parent_old, name_old, inode_parent_new, name_new):
        '''Rename a directory entry

        If *name_new* already exists, it should be overwritten.

        If the file system has received a `lookup`, but no `forget`
        call for the file that is about to be overwritten, `rename` is
        expected to only overwrite the directory entry and defer
        removal of the old inode with the its contents and metadata
        until the `forget` call is received.
        '''

        raise FUSEError(errno.ENOSYS)

    def link(self, inode, new_parent_inode, new_name):
        '''Create a hard link.

        The method must return an `EntryAttributes` instance with the
        attributes of the newly created directory entry.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def open(self, inode, flags):
        '''Open a file.

        *flags* will be a bitwise or of the open flags described in
        the :manpage:`open(2)` manpage and defined in the `os` module
        (with the exception of ``O_CREAT``, ``O_EXCL``, ``O_NOCTTY``
        and ``O_TRUNC``)

        This method should return an integer file handle. The file
        handle will be passed to the `read`, `write`, `flush`, `fsync`
        and `release` methods to identify the open file.
        '''

        raise FUSEError(errno.ENOSYS)

    def read(self, fh, off, size):
        '''Read *size* bytes from *fh* at position *off*

        This function should return exactly the number of bytes
        requested except on EOF or error, otherwise the rest of the
        data will be substituted with zeroes.
        '''

        raise FUSEError(errno.ENOSYS)

    def write(self, fh, off, buf):
        '''Write *buf* into *fh* at *off*

        This method should return the number of bytes written. If no
        error occured, this should be exactly :samp:`len(buf)`.
        '''

        raise FUSEError(errno.ENOSYS)

    def flush(self, fh):
        '''Handle close() syscall.

        This method is called whenever a file descriptor is closed. It
        may be called multiple times for the same open file (e.g. if
        the file handle has been duplicated).

        If the file system implements locking, this method must clear
        all locks belonging to the file handle's owner.
        '''

        raise FUSEError(errno.ENOSYS)

    def release(self, fh):
        '''Release open file

        This method will be called when the last file descriptor of
        *fh* has been closed. Therefore it will be called exactly once
        for each `open` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def fsync(self, fh, datasync):
        '''Flush buffers for open file *fh*

        If *datasync* is true, only the file contents should be
        flushed (in contrast to the metadata about the file).
        '''

        raise FUSEError(errno.ENOSYS)

    def opendir(self, inode):
        '''Open a directory.

        This method should return an integer file handle. The file
        handle will be passed to the `readdir`, `fsyncdir`
        and `releasedir` methods to identify the directory.
        '''

        raise FUSEError(errno.ENOSYS)


    def readdir(self, fh, off):
        '''Read directory entries

        This method should return an iterator over the contents of
        directory *fh*, starting at the entry identified by *off*.
        Directory entries must be of type `bytes`.

        The iterator must yield tuples of the form :samp:`({name}, {attr},
        {next_})`, where *attr* is an `EntryAttributes` instance and
        *next_* gives an offset that can be passed as *off* to start
        a successive `readdir` call at the right position.

        Iteration may be stopped as soon as enough elements have been
        retrieved. The method should be prepared for this case.

        If entries are added or removed during a `readdir` cycle, they
        may or may not be returned. However, they must not cause other
        entries to be skipped or returned more than once.

        :file:`.` and :file:`..` entries may be included but are not
        required.
        '''

        raise FUSEError(errno.ENOSYS)

    def releasedir(self, fh):
        '''Release open directory

        This method must be called exactly once for each `opendir` call.
        '''

        raise FUSEError(errno.ENOSYS)

    def fsyncdir(self, fh, datasync):
        '''Flush buffers for open directory *fh*

        If *datasync* is true, only the directory contents should be
        flushed (in contrast to metadata about the directory itself).
        '''

        raise FUSEError(errno.ENOSYS)

    def statfs(self):
        '''Get file system statistics

        The method is expected to return an appropriately filled
        `StatvfsData` instance.
        '''

        raise FUSEError(errno.ENOSYS)

    def stacktrace(self):
        '''Asynchronous debugging

        This method will be called when the ``fuse_stacktrace`` extended
        attribute is set on the mountpoint. It will be called without
        holding the global lock. The default implementation logs the
        current stack trace of every running Python thread. This can be
        quite useful to debug file system deadlocks.
        '''

        import sys
        import traceback

        code = list()
        for threadId, frame in sys._current_frames().items():
            code.append("\n# ThreadID: %s" % threadId)
            for filename, lineno, name, line in traceback.extract_stack(frame):
                code.append('%s:%d, in %s' % (os.path.basename(filename), lineno, name))
                if line:
                    code.append("    %s" % (line.strip()))

        log.error("\n".join(code))

    def setxattr(self, inode, name, value):
        '''Set an extended attribute.

        The attribute may or may not exist already.
        '''

        raise FUSEError(errno.ENOSYS)

    def getxattr(self, inode, name):
        '''Return extended attribute value

        If the attribute does not exist, the method must raise
        `FUSEError` with an error code of `ENOATTR`.
        '''

        raise FUSEError(errno.ENOSYS)

    def listxattr(self, inode):
        '''Get list of extended attribute names'''

        raise FUSEError(errno.ENOSYS)

    def removexattr(self, inode, name):
        '''Remove extended attribute

        If the attribute does not exist, the method must raise
        `FUSEError` with an error code of `ENOATTR`.
        '''

        raise FUSEError(errno.ENOSYS)


    def access(self, inode, mode, ctx):
        '''Check if requesting process has *mode* rights on *inode*.

        *ctx* will be a `RequestContext` instance. The method
        must return a boolean value.

        If the ``default_permissions`` mount option is given, this method is not
        called.
        '''

        raise FUSEError(errno.ENOSYS)

    def create(self, inode_parent, name, mode, flags, ctx):
        '''Create a file with permissions *mode* and open it with *flags*

        *ctx* will be a `RequestContext` instance.

        The method must return a tuple of the form *(fh, attr)*,
        where *fh* is a file handle like the one returned by `open`
        and *attr* is an `EntryAttributes` instance with the
        attributes of the newly created directory entry.

        Once an inode has been returned by `lookup`, `create`,
        `symlink`, `link`, `mknod` or `mkdir`, it must be kept by the
        file system until it receives a `forget` request for the
        inode. If `unlink` or `rmdir` requests are received prior to
        the `forget` call, they are expect to remove only the
        directory entry for the inode and defer removal of the inode
        itself until the `forget` call.
        '''

        raise FUSEError(errno.ENOSYS)
