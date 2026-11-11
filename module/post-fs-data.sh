#!/system/bin/sh

MODDIR=${0%/*}

chcon u:object_r:zygote_exec:s0 "$MODDIR/system/system_ext/bin/hyos_spawner" 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/system_ext/lib64/*.so 2>/dev/null
chcon u:object_r:system_lib_file:s0 "$MODDIR"/system/lib64/*.so 2>/dev/null
setprop rust.runtime_version 1.5.0
