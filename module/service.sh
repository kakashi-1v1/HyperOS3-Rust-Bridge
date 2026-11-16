#!/system/bin/sh

MODDIR=${0%/*}

chcon u:object_r:zygote_exec:s0 "$MODDIR/system/system_ext/bin/hyos_spawner" 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/system_ext/lib64/*.so 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/lib64/*.so 2>/dev/null

setprop rust.runtime_version 1.5.0

# KernelSU: some mount metamodules (e.g. Hybrid Mount) put module mount points on the kernel umount list, which hides
# them from every app without root - the launcher then can't load this runtime ("libmisqlite3.so not found").
# Take this module's own mount points off that list (only paths this module provides; other modules' stay).
keep_mounts() {
  K=""
  for k in /data/adb/ksud /data/adb/ksu/bin/ksud; do [ -x "$k" ] && { K=$k; break; }; done
  [ -n "$K" ] || return 0
  "$K" umount list 2>/dev/null | awk 'NR > 2 { print $1 }' | while read -r p; do
    case "$p" in /*) ;; *) continue ;; esac
    if [ -e "$MODDIR$p" ] || [ -e "$MODDIR/system$p" ]; then
      "$K" umount remove "$p" >/dev/null 2>&1
    fi
  done
}
keep_mounts
# again once booted: some metamodules register their umount list late
( until [ "$(getprop sys.boot_completed)" = 1 ]; do sleep 2; done; sleep 5; keep_mounts ) &

i=0
while [ "$i" -lt 30 ]; do
  if [ "$(getprop init.svc.zygote)" = "running" ]; then
    break
  fi
  sleep 1
  i=$((i + 1))
done

if [ "$(getprop rust.runtime_active)" = "1" ]; then
  start hyos_spawner >/dev/null 2>&1
fi
