#!/usr/bin/env python3
"""Patch HyperOS 3 runtime 1.5.0 libhyper_os_app_public.so so the HyperOS 4 Flutter engine can find the
rust_app_libs linker namespace (see kashins.c). The slot page is file-backed (.gnu_debugdata), hence the marker.. usage: patch_app_public.py in.so out.so"""
import hashlib, struct, sys
SHA1 = 'cd837a792cf27e7847d5e926138e804b531f2960'
HOOK, CAVE, SLOT = 0x67bb0, 0x74060, 0x80800
src, dst = sys.argv[1:3]
d = bytearray(open(src, 'rb').read())
assert hashlib.sha1(d).hexdigest() == SHA1, 'unexpected libhyper_os_app_public.so build'
w = lambda off: struct.unpack_from('<I', d, off)[0]
assert w(HOOK) == 0x390002ff, 'hook site is not strb wzr,[x23]'
assert w(HOOK - 4) == 0x34000000 | (((0x69764 - 0x67bac) >> 2) << 5) | 0, 'unexpected code before hook'
assert not any(d[CAVE:CAVE + 32]), 'cave not empty'
def adrp(rd, pc, t):
    imm = (t >> 12) - (pc >> 12)
    return 0x90000000 | ((imm & 3) << 29) | (((imm >> 2) & 0x7ffff) << 5) | rd
cave = [adrp(16, CAVE, SLOT & ~0xfff),
        0xf9000000 | (((SLOT & 0xfff) >> 3) << 10) | (16 << 5) | 21,      # str x21, [x16, #0x800]
        0x52800011 | (0x5348 << 5),                                      # movz w17, #0x5348
        0x72a00011 | (0x4b41 << 5),                                      # movk w17, #0x4b41, lsl #16
        0xf9000000 | ((((SLOT & 0xfff) + 8) >> 3) << 10) | (16 << 5) | 17,  # str x17, [x16, #0x808] ('KASH' marker)
        0x390002ff,                                                      # strb wzr, [x23] (moved)
        0x14000000 | (((HOOK + 4 - (CAVE + 24)) >> 2) & 0x3ffffff)]      # b HOOK+4
struct.pack_into('<%dI' % len(cave), d, CAVE, *cave)
struct.pack_into('<I', d, HOOK, 0x14000000 | (((CAVE - HOOK) >> 2) & 0x3ffffff))
old, new = b'libsysinfo.dylib.so\0', b'libkashins.dylib.so\0'
assert d.count(old) == 1
i = d.index(old); d[i:i + len(new)] = new
open(dst, 'wb').write(d)
print('patched', dst, hashlib.sha1(d).hexdigest())
