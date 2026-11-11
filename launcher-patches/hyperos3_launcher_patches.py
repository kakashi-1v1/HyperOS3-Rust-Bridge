#!/usr/bin/env python3
"""Optional / educational: HyperOS 3 patches for the HyperOS 4 launcher 8.01.02.9239 (libapp.so, Dart AOT).

These are NOT needed for the launcher to start on HyperOS 3 (the bridge does that). They change recents behaviour
that relies on HyperOS 4-only system features. They are experiments, published so others can continue them; read
docs/status.md before using them. A launcher patched with them is meant for HyperOS 3 only.

Every patch replaces whole instructions in place (no code caves) and checks the original instruction first, so it
works on the stock 9239 APK and on the HyperOS 4 Rust Launcher Mod v1.1 (whose libapp.so keeps these sites stock).

Patches (addresses are libapp.so file offsets = virtual addresses):

  --recents  (default on) recents quick switch on HyperOS 3:
      0x1167424  TaskFlightAnimationDriver.disallowActiveAppWindowFinish -> return null
                 (the tap no longer blocks finishing the app->recents transition)
      0x11659dc  RecentsViewController.finishWindowToRecents: tbnz w1,#4 -> b
                 (don't skip the finish while "launching from app-to-recents")
      0x1165b34  its delayed (~50 ms) closure: tbnz w0,#4 -> b        (same check, "during delay")
      0x1165bc0  its delayed closure: b.eq -> b                        ("new transition started during delay")
      Effect: the tapped app is no longer merged into the app->recents transition, but the delayed finish's cleanup
      still clears the launch's opening callback, so the app may still open without animation.

  --finish-now  (default off) also finish immediately instead of after ~50 ms:
      0x1165ad4  finishWindowToRecents: after loading the context, branch to the delayed closure's tail
                 (0x1165c14: load its fields, call _finishRemoteTransitionToRecents, return)
      Effect: quick switch animates, BUT every swipe into recents finishes early and the current task card flickers.
      A version that only finishes early after a card tap needs a writable flag (open problem, see docs/status.md).

  --stack  (default on) DeviceConfig.supportsStackStyle -> true (Stack recents layout on every device)
      0x97b374  add x0, x22, #32 ; ret

Input: an APK (libapp.so stored uncompressed, patched in place, CRCs updated) or a bare libapp.so.
The output APK keeps its old signature block, so signature verification must be disabled (core patch), as for any
modified system launcher.

usage: hyperos3_launcher_patches.py IN OUT [--no-recents] [--finish-now] [--no-stack]
"""
import argparse, struct, sys, zlib

TRUE_RET = [0x910082c0, 0xd65f03c0]           # add x0, x22, #32 (true) ; ret
NULL_RET = [0xaa1603e0, 0xd65f03c0]           # mov x0, x22 (null) ; ret
PROLOGUE = [0xa9bf79fd, 0xaa0f03fd]           # stp x29, x30, [x15, #-16]! ; mov x29, x15

PATCHES = {
    'recents': [
        (0x1167424, PROLOGUE, NULL_RET, 'disallowActiveAppWindowFinish -> return'),
        (0x11659dc, [0x372001a1], [0x1400000d], 'finishWindowToRecents: always finish (b +52)'),
        (0x1165b34, [0x372002a0], [0x14000015], 'delayed finish: launching check -> b +84'),
        (0x1165bc0, [0x540002a0], [0x14000015], 'delayed finish: generation check -> b +84'),
    ],
    'finish_now': [
        (0x1165ad4, [0x9140eb61], [0x14000050], 'finishWindowToRecents: finish now (b 0x1165c14)'),
    ],
    'stack': [
        (0x97b374, PROLOGUE, TRUE_RET, 'supportsStackStyle -> true'),
    ],
}
SANITY = [(0x1165c14, 0xaa0203e0)]            # delayed closure tail used by --finish-now


def patch_so(so, wanted):
    so = bytearray(so)
    rd = lambda a: struct.unpack_from('<I', so, a)[0]
    for a, w in SANITY:
        if rd(a) != w:
            sys.exit(f'not the 9239 libapp.so (0x{a:x} = {rd(a):08x})')
    for key in wanted:
        for addr, orig, new, label in PATCHES[key]:
            live = [rd(addr + 4 * i) for i in range(len(orig))]
            if live == new:
                print(f'  0x{addr:x} already patched: {label}')
                continue
            if live != orig:
                sys.exit(f'0x{addr:x}: unexpected {" ".join("%08x" % x for x in live)} ({label})')
            for i, w in enumerate(new):
                struct.pack_into('<I', so, addr + 4 * i, w)
            print(f'  0x{addr:x} {label}')
    return bytes(so)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src'); ap.add_argument('dst')
    ap.add_argument('--no-recents', action='store_true')
    ap.add_argument('--finish-now', action='store_true')
    ap.add_argument('--no-stack', action='store_true')
    a = ap.parse_args()
    wanted = ([] if a.no_recents else ['recents']) + (['finish_now'] if a.finish_now else []) + \
             ([] if a.no_stack else ['stack'])
    data = bytearray(open(a.src, 'rb').read())
    if data[:4] != b'PK\x03\x04':
        open(a.dst, 'wb').write(patch_so(data, wanted))
        print('wrote', a.dst); return
    # APK: find the stored lib/arm64-v8a/libapp.so, patch it in place, fix both CRCs
    name = b'lib/arm64-v8a/libapp.so'
    eocd = data.rfind(b'PK\x05\x06')
    n, cd_size, cd_off = struct.unpack_from('<HII', data, eocd + 10)
    p = cd_off
    for _ in range(n):
        method, = struct.unpack_from('<H', data, p + 10)
        csize, usize = struct.unpack_from('<II', data, p + 20)
        nl, el, cl = struct.unpack_from('<HHH', data, p + 28)
        lho, = struct.unpack_from('<I', data, p + 42)
        if data[p + 46:p + 46 + nl] == name:
            if method != 0:
                sys.exit('libapp.so is compressed in this APK; extract it, patch the .so and repack')
            lnl, lel = struct.unpack_from('<HH', data, lho + 26)
            start = lho + 30 + lnl + lel
            so = patch_so(data[start:start + usize], wanted)
            data[start:start + usize] = so
            crc = zlib.crc32(so) & 0xffffffff
            struct.pack_into('<I', data, lho + 14, crc)
            struct.pack_into('<I', data, p + 16, crc)
            open(a.dst, 'wb').write(data)
            print('wrote', a.dst); return
        p += 46 + nl + el + cl
    sys.exit('lib/arm64-v8a/libapp.so not found in the APK')


if __name__ == '__main__':
    main()
