from posix.types cimport (blkcnt_t, blksize_t, dev_t, gid_t, ino_t, mode_t,
                          nlink_t, off_t, time_t, uid_t)

IF UNAME_MACHINE in ('mips', 'mipsel'):
    cdef extern from "<sys/stat.h>" nogil:
        cdef struct struct_stat "stat":
            unsigned st_dev
            ino_t   st_ino
            mode_t  st_mode
            nlink_t st_nlink
            uid_t   st_uid
            gid_t   st_gid
            unsigned st_rdev
            off_t   st_size
            blksize_t st_blksize
            blkcnt_t st_blocks
            time_t  st_atime
            time_t  st_mtime
            time_t  st_ctime
            time_t  st_birthtime
ELSE:
    cdef extern from "<sys/stat.h>" nogil:
        cdef struct struct_stat "stat":
            dev_t   st_dev
            ino_t   st_ino
            mode_t  st_mode
            nlink_t st_nlink
            uid_t   st_uid
            gid_t   st_gid
            dev_t   st_rdev
            off_t   st_size
            blksize_t st_blksize
            blkcnt_t st_blocks
            time_t  st_atime
            time_t  st_mtime
            time_t  st_ctime
            time_t  st_birthtime
