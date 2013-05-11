#!/usr/bin/env python3
'''
passthroughfs.py - Example file system for python-llfuse

This file system just mirrors the contents of a specified directory
tree.

Copyright (C) Nikolaus Rath <Nikolaus@rath.org>

This file is part of python-llfuse (http://python-llfuse.googlecode.com).
python-llfuse can be distributed under the terms of the GNU LGPL.
'''

import os
import sys

# We are running from the llfuse source directory, make sure
# that we use modules from this directory
basedir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
if (os.path.exists(os.path.join(basedir, 'setup.py')) and
    os.path.exists(os.path.join(basedir, 'src', 'llfuse.pyx'))):
    sys.path = [os.path.join(basedir, 'src')] + sys.path
    
    
import llfuse
from argparse import ArgumentParser
import errno
import stat
import logging
from llfuse import FUSEError

log = logging.getLogger()
fse = sys.getfilesystemencoding()

def bytes2str(s):
    return s.decode(fse, 'surrogateescape')

def str2bytes(s):
    return s.encode(fse, 'surrogateescape')


class Operations(llfuse.Operations):
    
    def __init__(self, source):      
        super(Operations, self).__init__()
        self.source = source
        self.inode_path_map = dict()
        self.path_inode_map = dict()
                    
    def lookup(self, inode_p, name):
        name = bytes2str(name)
        parent = self.path_inode_map[inode_p]
        path = os.path.join(parent, name)
        
        try:
            stat = os.lstat(path)
        except OSError as exc:
            raise FUSEError(exc.errno)
        
        if name != b'.' and name != b'..':
            self.inode_path_map[stat.ST_INO] = path
            self.path_inode_map[path] = stat.ST_INO
        
        return self.getattr(stat.ST_INO)

    def getattr(self, inode):
        path = self.inode_path_map[inode]
        try:
            stat = os.lstat(path)
        except OSError as exc:
            raise FUSEError(exc.errno)
        
        entry = llfuse.EntryAttributes()
        entry.st_ino = stat.ST_INO
        entry.st_mode = stat.ST_MODE
        entry.st_nlink = stat.ST_NLINK
        entry.st_uid = stat.ST_UID
        entry.st_gid = stat.ST_GID
        entry.st_rdev = stat.ST_DEV
        entry.st_size = stat.ST_SIZE        
        entry.st_atime = stat.ST_ATIME                          
        entry.st_mtime = stat.ST_MTIME
        entry.st_ctime = stat.ST_CTIME
        
        entry.generation = 0
        entry.entry_timeout = 5
        entry.attr_timeout = 5
        entry.st_blksize = 512
        entry.st_blocks = 1
        
        return entry

    def readlink(self, inode):
        path = self.inode_path_map[inode]
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise FUSEError(exc.errno)
        
        return str2bytes(target)
            
    def opendir(self, inode):
        return inode

    def readdir(self, inode, off):
        # FIXME
        pass

    def unlink(self, inode_p, name):
        name = bytes2str(name)
        parent = self.inode_path_map[inode_p]
        path = os.path.join(parent, name)
        try:
            os.unlink(path)
        except OSError as exc:
            raise FUSEError(exc.errno)

    def rmdir(self, inode_p, name):
        name = bytes2str(name)
        parent = self.inode_path_map[inode_p]
        path = os.path.join(parent, name)
        try:
            os.rmdir(path)
        except OSError as exc:
            raise FUSEError(exc.errno)

    def symlink(self, inode_p, name, target, ctx):
        name = bytes2str(name)
        target = bytes2str(target)
        parent = self.inode_path_map[inode_p]
        path = os.path.join(parent, name)
        try:
            os.symlink(target, path)
        except OSError as exc:
            raise FUSEError(exc.errno)
        
        stat = os.lstat(path)
        self.path_inode_map[path] = stat.ST_INO
        self.inode_path_map[stat.ST_INO] = path
        
        return self.getattr(stat.ST_INO)
        
    def rename(self, inode_p_old, name_old, inode_p_new, name_new):     
        name_old = bytes2str(name_old)
        name_new = bytes2str(name_new)
        parent_old = self.inode_path_map[inode_p_old]
        parent_new = self.inode_path_map[inode_p_new]
        path_old = os.path.join(parent_old, name_old)
        path_new = os.path.join(parent_new, name_new)
        try:
            os.rename(path_old, path_new)
        except OSError as exc:
            raise FUSEError(exc.errno)
        
        inode = self.path_inode_map[path_old]
        del self.path_inode_map[path_old]
        self.inode_path_map[inode] = path_new
        
    def link(self, inode, new_inode_p, new_name):
        new_name = bytes2str(new_name)
        parent = self.inode_path_map[new_inode_p]
        path = os.path.join(parent, new_name)
        try:
            os.link(self.inode_path_map[inode], path)
        except OSError as exc:
            raise FUSEError(exc.errno)

        self.path_inode_map[path] = inode
        self.inode_path_map[inode] = path
        
        return self.getattr(inode)

    def setattr(self, inode, attr):

        if attr.st_size is not None:
            data = self.get_row('SELECT data FROM inodes WHERE id=?', (inode,))[0]
            if data is None:
                data = ''
            if len(data) < attr.st_size:
                data = data + '\0' * (attr.st_size - len(data))
            else:
                data = data[:attr.st_size]
            self.cursor.execute('UPDATE inodes SET data=?, size=? WHERE id=?',
                                (buffer(data), attr.st_size, inode))
        if attr.st_mode is not None:
            self.cursor.execute('UPDATE inodes SET mode=? WHERE id=?',
                                (attr.st_mode, inode))

        if attr.st_uid is not None:
            self.cursor.execute('UPDATE inodes SET uid=? WHERE id=?',
                                (attr.st_uid, inode))

        if attr.st_gid is not None:
            self.cursor.execute('UPDATE inodes SET gid=? WHERE id=?',
                                (attr.st_gid, inode))

        if attr.st_rdev is not None:
            self.cursor.execute('UPDATE inodes SET rdev=? WHERE id=?',
                                (attr.st_rdev, inode))

        if attr.st_atime is not None:
            self.cursor.execute('UPDATE inodes SET atime=? WHERE id=?',
                                (attr.st_atime, inode))

        if attr.st_mtime is not None:
            self.cursor.execute('UPDATE inodes SET mtime=? WHERE id=?',
                                (attr.st_mtime, inode))

        if attr.st_ctime is not None:
            self.cursor.execute('UPDATE inodes SET ctime=? WHERE id=?',
                                (attr.st_ctime, inode))

        return self.getattr(inode)

    def mknod(self, inode_p, name, mode, rdev, ctx):
        return self._create(inode_p, name, mode, ctx, rdev=rdev)

    def mkdir(self, inode_p, name, mode, ctx):
        return self._create(inode_p, name, mode, ctx)

    def statfs(self):
        stat_ = llfuse.StatvfsData()

        stat_.f_bsize = 512
        stat_.f_frsize = 512

        size = self.get_row('SELECT SUM(size) FROM inodes')[0]
        stat_.f_blocks = size // stat_.f_frsize
        stat_.f_bfree = max(size // stat_.f_frsize, 1024)
        stat_.f_bavail = stat_.f_bfree

        inodes = self.get_row('SELECT COUNT(id) FROM inodes')[0]
        stat_.f_files = inodes
        stat_.f_ffree = max(inodes , 100)
        stat_.f_favail = stat_.f_ffree

        return stat_

    def open(self, inode, flags):
        # Yeah, unused arguments
        #pylint: disable=W0613
        self.inode_open_count[inode] += 1
        
        # Use inodes as a file handles
        return inode

    def access(self, inode, mode, ctx):
        # Yeah, could be a function and has unused arguments
        #pylint: disable=R0201,W0613
        return True

    def create(self, inode_parent, name, mode, flags, ctx):
        entry = self._create(inode_parent, name, mode, ctx)
        self.inode_open_count[entry.st_ino] += 1
        return (entry.st_ino, entry)

    def _create(self, inode_p, name, mode, ctx, rdev=0, target=None):             
        if self.getattr(inode_p).st_nlink == 0:
            log.warn('Attempted to create entry %s with unlinked parent %d',
                     name, inode_p)
            raise FUSEError(errno.EINVAL)

        self.cursor.execute('INSERT INTO inodes (uid, gid, mode, mtime, atime, '
                            'ctime, target, rdev) VALUES(?, ?, ?, ?, ?, ?, ?, ?)',
                            (ctx.uid, ctx.gid, mode, time(), time(), time(), target, rdev))

        inode = self.cursor.lastrowid
        self.db.execute("INSERT INTO contents(name, inode, parent_inode) VALUES(?,?,?)",
                        (name, inode, inode_p))
        return self.getattr(inode)


    def read(self, fh, offset, length):
        data = self.get_row('SELECT data FROM inodes WHERE id=?', (fh,))[0]
        if data is None:
            data = ''
        return data[offset:offset+length]

                
    def write(self, fh, offset, buf):
        data = self.get_row('SELECT data FROM inodes WHERE id=?', (fh,))[0]
        if data is None:
            data = ''
        data = data[:offset] + buf + data[offset+len(buf):]
        
        self.cursor.execute('UPDATE inodes SET data=?, size=? WHERE id=?',
                            (buffer(data), len(data), fh))
        return len(buf)
   
    def release(self, fh):
        self.inode_open_count[fh] -= 1

        if self.inode_open_count[fh] == 0:
            del self.inode_open_count[fh]
            if self.getattr(fh).st_nlink == 0:
                self.cursor.execute("DELETE FROM inodes WHERE id=?", (fh,))

def init_logging(debug=False):
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d %(threadName)s: '
                                  '[%(name)s] %(message)s', datefmt="%Y-%m-%d %H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    root_logger = logging.getLogger()
    if debug:
        handler.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.DEBUG)            
    else:
        handler.setLevel(logging.INFO)
        root_logger.setLevel(logging.INFO)    
    root_logger.addHandler(handler)    
        
        
def parse_args(args):
    '''Parse command line'''

    parser = ArgumentParser()

    parser.add_argument('source', type=str,
                        help='Directory tree to mirror')
    parser.add_argument('mountpoint', type=str,
                        help='Where to mount the file system')

    parser.add_argument('--single', type=bool, default=False,
                        help='Run single threaded')
    
    parser.add_argument('--debug', type=bool, default=False,
                        help='Enable debugging output')

    return parser.parse_args(args)
        
          
def main():    
    options = parse_args(sys.argv[1:])
    init_logging(options.debug)
    operations = Operations(options.source)
    
    log.debug('Mounting...')
    llfuse.init(operations, options.mountpoint, 
                [  b'fsname=passthroughfs', b"nonempty" ])
    
    try:
        log.debug('Entering main loop..')
        llfuse.main(options.single)
    except:
        llfuse.close(unmount=False)
        raise

    log.debug('Unmounting..')
    llfuse.close()
    

if __name__ == '__main__':
    main()
