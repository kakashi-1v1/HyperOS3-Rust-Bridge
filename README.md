# HyperOS 3 Rust Bridge

A Magisk / KernelSU / APatch module that lets **HyperOS 4 Rust/Flutter apps** (the new `com.miui.home` launcher is the
reference) start on **HyperOS 3**.

HyperOS 4 moved apps like the launcher to a Rust runtime (`hyos_spawner`, `libhyper_os_*`) and a Flutter engine
(`libhyper_os_flutter.so`). HyperOS 3 ships an older runtime and engine, so HyperOS 4 apps crash there. This bridge
installs a runtime HyperOS 3 can host, the HyperOS 4 engine, and a few binary patches plus a small shim library
(`libkashins.dylib.so`) that fill the gaps between the two.

> **Status: experimental, community project.** The HyperOS 4 launcher (8.01.02.9239) boots and is usable on HyperOS 3
> with this bridge, but several HyperOS 4 system features have no HyperOS 3 counterpart (see [docs/status.md](docs/status.md)).
> The [HyperOS 4 Rust Launcher Mod](https://github.com/Mods-Center/HyperOS-Rust-Launcher-Mod) does **not** support
> HyperOS 3. This repository exists so others can study and extend the bridge. Contributions are welcome
> ([CONTRIBUTING.md](CONTRIBUTING.md)). Experimental launcher-side patches for HyperOS 3 are in
> [launcher-patches/](launcher-patches/) (optional, educational).

## What it contains

| Part | What it does |
|---|---|
| HyperOS Rust runtime 1.5.0 (`hyos_spawner`, `libhyper_os_*`, `hyperos.rustruntime.jar`) | Starts Rust apps through `hyos_spawner`; the permissions XML declares `hyperos.rustruntime.v3/v4/v5` (HyperOS 4 apps require v5) |
| HyperOS 4 `libhyper_os_flutter.so` | HyperOS 3's engine (Dart 3.7) can't run HyperOS 4 snapshots |
| HyperOS 4 `libmisqlite3.so`, `librust_maml_sdk.so` | Missing on HyperOS 3; the launcher links against them |
| `libhyper_os_app_public.so` (patched) | Saves the `rust_app_libs` linker namespace so the engine can load app libraries into it |
| `libkashins.dylib.so` (shim, source in `shim/`) | Exports `get_rust_app_namespace` and the `ComputilityLevel_*` device-level functions HyperOS 4 apps look up |
| `libhyper_os_service_manager.dylib.so` (patched) | Uses HyperOS 3's name for the cust-feature service |
| `libhyper_os_security_public.so` (patched) | Self-permission checks that fail with a parcel mismatch count as granted |

How each piece works, with addresses, is in [docs/how-it-works.md](docs/how-it-works.md).

## Install

1. HyperOS 3 (Android 15/16), arm64, Magisk / KernelSU / APatch.
2. Flash the ready-made `HyperOS3_RustBridge_vX.Y.zip` from the [releases](../../releases) and reboot.
3. Install the HyperOS 4 Rust app you want to try. For a system app such as the launcher, signature verification has
   to be disabled (core patch), exactly as on HyperOS 4.

The module refuses to install on HyperOS 4 (not needed there) and removes the older
`hyperos_rustruntime_v4_minimal` module, which it replaces.

To remove: remove the module (and any HyperOS 4 app that depends on it) and reboot.

## Build it yourself

```
tools/build_bridge.sh RUNTIME_DIR OS4_LIBS_DIR [OUT_ZIP]
```

- `RUNTIME_DIR`: the HyperOS Rust runtime 1.5.0 files, laid out like the device (`system_ext/bin/hyos_spawner`,
  `system_ext/lib64/*.so`, `system_ext/framework/hyperos.rustruntime.jar`, `system/lib64/libhex.dylib.so`,
  `system/lib64/libsysinfo.dylib.so`).
- `OS4_LIBS_DIR`: `libhyper_os_flutter.so`, `libmisqlite3.so`, `librust_maml_sdk.so` from a HyperOS 4 device/ROM
  (`/system_ext/lib64`).

The patch scripts check the SHA-1 of every input library, so they only touch the exact builds they were written
for. The script copies, patches and builds the shim, then zips the module. Needs `python3`, `clang` (NDK or
Termux) and `zip`. The Xiaomi binaries are not stored in this repository; the release zip contains them.

## Repository layout

| Path | What |
|---|---|
| `module/` | Module scripts (Dynamic Installer by @BlassGO), init rc, permissions XML; binaries are added by the build |
| `shim/` | `kashins.c`, the shim library, and its build script |
| `patches/` | Binary patches for the runtime 1.5.0 libraries (Python, SHA-1 checked) |
| `tools/` | `build_bridge.sh` |
| `launcher-patches/` | Optional, educational HyperOS 3 patches for the launcher's recents ([README](launcher-patches/README.md)) |
| `docs/` | How it works, current status, list of HyperOS 4 runtime functions missing on HyperOS 3 |

## Credits

- **🅺🅰🆂🅷🅸** ([@kakashi1v1](https://t.me/kakashi1v1)): bridge, patches, shim, documentation
- The original **HyperOS Rust Runtime v4 Minimal** module (author listed as "Codex"): the runtime 1.5.0 file set and
  the `hyos_spawner` init/SELinux setup this bridge builds on
- **Dynamic Installer** by @BlassGO: module installer framework
- **Claude** (Anthropic): reverse engineering and patch development, directed and tested on a real device by the
  author

## Disclaimer

Not affiliated with or endorsed by Xiaomi. HyperOS, MIUI and the included runtime libraries are Xiaomi's property.
Use at your own risk; keep a way to remove modules from recovery or safe mode.
