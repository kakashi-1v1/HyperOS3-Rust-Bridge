# How the bridge works

Reference app: HyperOS 4 launcher `com.miui.home` 8.01.02.9239. Test device: Redmi (peridot), HyperOS
OS3.0.305.0.WNPCNXM (Android 16). Everything below was found from logcat, tombstones and disassembly on that device.

## 1. Runtime and engine

HyperOS 4 apps are started by `hyos_spawner`, which loads the app's `libapp_launcher.so` (Rust) and the Flutter
engine `libhyper_os_flutter.so`, which runs `libapp.so` (Dart AOT).

| | HyperOS 3 stock | Bridge |
|---|---|---|
| Rust runtime | `hyos_spawner` + `libhyper_os_*` 1.x | runtime 1.5.0 file set (from the "v4 minimal" module) |
| uses-library | `hyperos.rustruntime.v3` | v3, v4, v5 → `/system_ext/framework/hyperos.rustruntime.jar` |
| Flutter engine | Dart 3.7.0 (can't load HyperOS 4 snapshots) | HyperOS 4 engine, Dart 3.10.1 |
| `libmisqlite3.so`, `librust_maml_sdk.so` | missing | from HyperOS 4 |

`service.sh` / `post-fs-data.sh` label `hyos_spawner` as `zygote_exec`, the libraries as `system_lib_file`, set
`rust.runtime_version` and start `hyos_spawner` if the overlay was mounted after init parsed its rc file.

The HyperOS 4 engine and maml library resolve all their imports against runtime 1.5.0 (checked with `llvm-nm`).

## 2. Linker namespace (`get_rust_app_namespace`)

**Symptom:** `librust_maml_sdk` panics with `called Result::unwrap() on an Err value: runtime not set`.

The Rust part of the app links `librust_maml_sdk.so` and calls `maml_set_runtime`. The Dart side loads the same
library through the engine's `TryLoadFromRustAppNamespace`, which calls
`dlsym(libhyper_os_app_public.so, "get_rust_app_namespace")` and opens the library in that namespace. Runtime 1.5.0
creates the namespace (`rust_app_libs`) in `launch_main_thread` but has no getter, so the engine fell back to plain
`dlopen` and got a second copy of the library without a runtime.

**Fix:** `patches/patch_app_public.py` (input SHA-1 `cd837a79…`):

- `0x67bb0` (`strb wzr,[x23]`, right after `link_namespaces` succeeded) → branch to a code cave at `0x74060`, which
  stores `x21` (the raw `android_namespace_t*`; `Namespace::as_raw` is the identity) at `0x80800`, writes the marker
  `"KASH"` at `0x80808`, runs the moved instruction and branches back. `0x80800` is in the page after `.data`; that
  page is file-backed (`.gnu_debugdata`), hence the marker.
- The `DT_NEEDED` entry `libsysinfo.dylib.so` is renamed to `libkashins.dylib.so` (same length). The shim depends on
  the real `libsysinfo.dylib.so`, so nothing is lost, and `dlsym` on the app_public handle now also searches the shim.

`shim/kashins.c` exports `get_rust_app_namespace`: it finds app_public with `dl_iterate_phdr`, checks the hook
instruction and the marker, and returns the saved pointer (or NULL, which makes the engine behave as before).

## 3. Service name

**Symptom:** abort in `Hyper_os_cust_feature_resolve_get_bool` → `ServiceManager::hyper_os_cust_feature_resolve` →
`unwrap()` on `NAME_NOT_FOUND`.

Runtime 1.5.0 looks the service up as `hyper_os_cust_feature_resolve`; HyperOS 3 registers it as
`HyperOSCustFeatureResolve` (same AIDL descriptor `miui.os.IHyperOSCustFeatureResolve`).

**Fix:** `patches/patch_service_manager.py`: the name at `0x4130f` and the three `mov w9, #29` lengths before its
`adr` (`0x6e0cc`, `0x708d4`, `0x73174`) → 25.

## 4. Device level (`ComputilityLevel_*`)

HyperOS 4 apps look up many runtime functions with `dlsym(RTLD_DEFAULT, …)` and quietly disable features when one is
missing. bionic resolves `RTLD_DEFAULT` from a non-global library through the caller's whole dependency tree, and the
shim is in that tree (via app_public), so the shim can supply missing functions on HyperOS 3 only.

The launcher derives its device level from `ComputilityLevel_get_computility_level_v2`; without it the device counts
as low end (no stack recents etc.). The shim implements the four functions like HyperOS 4's `miui_booster_private`:

- v1: `persist.sys.computility.{version (2024..2050), cpulevel (1..6), gpulevel (1..6)}`, level = min(cpu, gpu)
- v2: `persist.sys.computilityV2.{version, cpulevel, gpulevel, devicelevel (1..4)}`, level = devicelevel
- HyperOS 3 has no V2 properties, so v2 is derived from v1: `clamp(v1 - 1, 1, 4)` (v1 4 → v2 3, "high")

## 5. Lock state (`SUBSCRIBE_TO_KEYGUARD_LOCKED_STATE`)

**Symptom:** after every boot the launcher believes the screen is locked (`is_keyguard_locked=true`): no recents,
every gesture is handed to the keyguard handler, odd open/close animations. Restarting the launcher while unlocked
"fixes" it until the next boot.

Runtime 1.5.0's `check_self_permission` calls `checkPermissionForDevice`, which HyperOS 3's system answers with
`EX_BAD_PARCELABLE` ("Parcel data not fully consumed"). The launcher's `KeyguardLockedWatcher` treats that as "no
permission", never subscribes to lock/unlock events and keeps the state it read at start (locked, at boot).

**Fix:** `patches/patch_security_public.py`: the exported wrapper `PermissionManager_check_self_permission`
(`0x456c`) returns `Ok(0)` (= `PERMISSION_GRANTED`) when the private call returns an error. A real "denied"
(`Ok(-1)`) is passed through. Note: the `Ok` value is the Android result code, so returning `Ok(1)` means denied.

## Where the files come from

- Runtime 1.5.0 file set: the "HyperOS Rust Runtime v4 Minimal" module (`hyperos_rustruntime_v4_minimal`), itself
  taken from a HyperOS build with that runtime.
- `libhyper_os_flutter.so`, `libmisqlite3.so`, `librust_maml_sdk.so`: `/system_ext/lib64` of a HyperOS 4 device
  (runtime 3.1.0). SHA-1 of the files used for the release: flutter `702c83cc…`, misqlite3 `ee6eedfd…`,
  maml `094e9eba…`.

## Debugging tips

- The log ring buffer is 128 KB on many ROMs and boot messages are gone quickly: `logcat -G 16M` before testing.
- Tombstones (`/data/tombstones`) keep the backtrace of each crash; Rust panics also log under the library's tag
  (e.g. `rust_maml_sdk`).
- Module files are often served from an image mounted at boot. To test a changed library without rebooting:
  `su -mm -c 'mount -o bind <new file> <live path>'`, then restart the app.
