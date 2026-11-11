#!/usr/bin/env bash
# Builds libkashins.dylib.so (arm64, 16 KB pages) with the NDK clang or Termux clang.
#   SYSINFO  path to libsysinfo.dylib.so from the runtime files (the shim links against it, see kashins.c)
#   OUT      output file (default: libkashins.dylib.so next to this script)
set -e
cd "$(dirname "$0")"
SYSINFO=${SYSINFO:?set SYSINFO to the runtime libsysinfo.dylib.so (system/lib64/libsysinfo.dylib.so)}
OUT=${OUT:-libkashins.dylib.so}
CC=${CC:-clang}
$CC --target=aarch64-linux-android29 -O2 -fPIC -shared -Wall \
    -o "$OUT" kashins.c \
    -Wl,-soname,libkashins.dylib.so -Wl,-z,max-page-size=16384 \
    -Wl,--no-as-needed "$SYSINFO"
echo "built $OUT"
