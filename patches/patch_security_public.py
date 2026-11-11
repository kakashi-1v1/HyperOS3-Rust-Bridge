#!/usr/bin/env python3
"""HyperOS 3 runtime 1.5.0: PermissionManager_check_self_permission fails on HyperOS 3 (checkPermissionForDevice ->
EX_BAD_PARCELABLE "Parcel data not fully consumed"). The launcher then thinks it lacks SUBSCRIBE_TO_KEYGUARD_LOCKED_STATE,
never subscribes to lock/unlock and stays "locked" after boot (no recents, keyguard gestures). Patched wrapper:
Err(..) -> Ok(0) = PERMISSION_GRANTED (the launcher is privileged; every permission it asks for is in its allowlist); Ok(x) unchanged.
usage: patch_security_public.py in.so out.so"""
import hashlib, struct, sys
F = 0x456c
ORIG = [0xd503233f, 0xa9bf7bfd, 0x910003fd, None, 0x92608009, 0x7200001f, 0x92608009, 0x9a9f1108, 0xaa090100,
        0xa8c17bfd, 0xd50323bf, 0xd65f03c0]
SHA1 = '098ac591b328ebc367a8087f7c7e06d487153c30'   # runtime 1.5.0 build this patch was written for
src, dst = sys.argv[1:3]
d = bytearray(open(src, 'rb').read())
assert hashlib.sha1(d).hexdigest() == SHA1, 'unexpected input build (sha1 mismatch)'
w = list(struct.unpack_from('<12I', d, F))
assert w[0] == 0xd503233f and w[1] == 0xa9bf7bfd and w[2] == 0x910003fd and w[3] >> 26 == 0x25, 'unexpected prologue'
assert w[5] == 0x7200001f and w[11] == 0xd65f03c0, [hex(x) for x in w]
new = w[:4] + [0x92608009,   # and  x9, x0, #0xffffffff00000001   (Ok value | err flag)
               0x7200001f,   # tst  w0, #1                        (Err?)
               0xd503201f,   # nop
               0x9a8913e0,   # csel x0, xzr, x9, ne               (Err -> Ok(0) = PERMISSION_GRANTED)
               0xa8c17bfd, 0xd50323bf, 0xd65f03c0, 0xd503201f]
struct.pack_into('<12I', d, F, *new)
open(dst, 'wb').write(d)
print('patched', dst)
