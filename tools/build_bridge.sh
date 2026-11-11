#!/usr/bin/env bash
# Assembles the flashable HyperOS 3 Rust Bridge module.
#
#   build_bridge.sh RUNTIME_DIR OS4_LIBS_DIR [OUT_ZIP]
#
#   RUNTIME_DIR   HyperOS Rust runtime 1.5.0 files laid out like the device:
#                   system_ext/bin/hyos_spawner
#                   system_ext/framework/hyperos.rustruntime.jar
#                   system_ext/lib64/*.so          (libhyper_os_*, libabi_stable.dylib.so, ...)
#                   system/lib64/libhex.dylib.so, system/lib64/libsysinfo.dylib.so
#                 (see docs/how-it-works.md, "Where the files come from")
#   OS4_LIBS_DIR  from a HyperOS 4 device or ROM (/system_ext/lib64):
#                   libhyper_os_flutter.so  libmisqlite3.so  librust_maml_sdk.so
#
# Needs: python3, clang (NDK or Termux), zip.
set -e
RUNTIME=${1:?runtime dir}; OS4=${2:?HyperOS 4 libs dir}
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=${3:-$HERE/HyperOS3_RustBridge.zip}
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

cp -r "$HERE/module/." "$WORK/"
rm -f "$WORK/system/README.md"
mkdir -p "$WORK/system/system_ext/bin" "$WORK/system/system_ext/framework" "$WORK/system/system_ext/lib64" "$WORK/system/lib64"
cp "$RUNTIME/system_ext/bin/hyos_spawner" "$WORK/system/system_ext/bin/"
cp "$RUNTIME/system_ext/framework/hyperos.rustruntime.jar" "$WORK/system/system_ext/framework/"
cp "$RUNTIME"/system_ext/lib64/*.so "$WORK/system/system_ext/lib64/"
cp "$RUNTIME"/system/lib64/*.so "$WORK/system/lib64/"

# HyperOS 4 engine + the two libraries HyperOS 3 doesn't have
for l in libhyper_os_flutter.so libmisqlite3.so librust_maml_sdk.so; do
    cp "$OS4/$l" "$WORK/system/system_ext/lib64/$l"
done

# binary patches of the runtime 1.5.0 libraries (each checks the input's SHA-1)
L=$WORK/system/system_ext/lib64
python3 "$HERE/patches/patch_app_public.py"      "$RUNTIME/system_ext/lib64/libhyper_os_app_public.so"            "$L/libhyper_os_app_public.so"
python3 "$HERE/patches/patch_service_manager.py" "$RUNTIME/system_ext/lib64/libhyper_os_service_manager.dylib.so" "$L/libhyper_os_service_manager.dylib.so"
python3 "$HERE/patches/patch_security_public.py" "$RUNTIME/system_ext/lib64/libhyper_os_security_public.so"       "$L/libhyper_os_security_public.so"

# the shim
SYSINFO="$RUNTIME/system/lib64/libsysinfo.dylib.so" OUT="$L/libkashins.dylib.so" bash "$HERE/shim/build.sh"

rm -f "$OUT"
(cd "$WORK" && zip -qr -9 "$OUT" .)
echo "wrote $OUT"
