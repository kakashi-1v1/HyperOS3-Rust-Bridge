`tools/build_bridge.sh` fills this tree with the runtime and HyperOS 4 binaries (not stored in git):

```
system/system_ext/bin/hyos_spawner
system/system_ext/framework/hyperos.rustruntime.jar
system/system_ext/lib64/*.so            runtime 1.5.0 (3 of them patched) + HyperOS 4 engine/misqlite3/maml + libkashins
system/lib64/libhex.dylib.so, libsysinfo.dylib.so
system/system_ext/etc/init/init.hyos_spawner.rc       (in git)
system/product/etc/permissions/hyperos.rustruntime_v4.xml   (in git)
```
