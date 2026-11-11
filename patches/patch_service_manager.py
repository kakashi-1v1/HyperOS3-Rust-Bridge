#!/usr/bin/env python3
"""HyperOS 3 registers the cust-feature service as "HyperOSCustFeatureResolve"; runtime 1.5.0's
libhyper_os_service_manager.dylib.so asks for "hyper_os_cust_feature_resolve" -> NAME_NOT_FOUND -> unwrap
panic (launcher: is_ai_hd_icon_supported). Same AIDL descriptor (miui.os.IHyperOSCustFeatureResolve).
usage: patch_service_manager.py in.so out.so"""
import hashlib, struct, sys
STR, OLD, NEW = 0x4130f, b'hyper_os_cust_feature_resolve', b'HyperOSCustFeatureResolve'
SITES = (0x6e0cc, 0x708d4, 0x73174)          # mov w9, #29 before each adr x8, STR
SHA1 = '04e57d31db9c87d438ebcc83ea80ad4052b9c771'   # runtime 1.5.0 build this patch was written for
src, dst = sys.argv[1:3]
d = bytearray(open(src, 'rb').read())
assert hashlib.sha1(d).hexdigest() == SHA1, 'unexpected input build (sha1 mismatch)'
assert d[STR:STR + len(OLD)] == OLD
mov = lambda imm: 0x52800009 | (imm << 5)
for s in SITES:
    assert struct.unpack_from('<I', d, s)[0] == mov(len(OLD)), hex(s)
    struct.pack_into('<I', d, s, mov(len(NEW)))
d[STR:STR + len(NEW)] = NEW
open(dst, 'wb').write(d)
print('patched', dst, hashlib.sha1(d).hexdigest())
