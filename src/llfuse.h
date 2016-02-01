/*
llfuse.h

Copyright © 2013 Nikolaus Rath <Nikolaus.org>

This file is part of Python-LLFUSE. This work may be distributed under
the terms of the GNU LGPL.
*/


#define PLATFORM_LINUX 1
#define PLATFORM_BSD 2
#define PLATFORM_DARWIN 3

#define PLATFORM PLATFORM_LINUX

#include <fuse.h>

#if FUSE_VERSION < 29
#error FUSE version too old, 2.9.0 or newer required
#endif

#if FUSE_MAJOR_VERSION != 2
#error This version of the FUSE library is not yet supported.
#endif
