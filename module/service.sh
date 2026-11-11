#!/system/bin/sh

MODDIR=${0%/*}

chcon u:object_r:zygote_exec:s0 "$MODDIR/system/system_ext/bin/hyos_spawner" 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/system_ext/lib64/*.so 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/lib64/*.so 2>/dev/null

setprop rust.runtime_version 1.5.0

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
