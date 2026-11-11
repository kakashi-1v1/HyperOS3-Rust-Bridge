# Contributing

Issues and pull requests are welcome, especially:

- **Missing runtime functions** ([docs/missing-symbols.md](docs/missing-symbols.md)): implement them in
  `shim/kashins.c` when HyperOS 3 offers an equivalent. The launcher looks them up with `dlsym(RTLD_DEFAULT, …)`,
  which reaches the shim on HyperOS 3 only.
- **Other HyperOS 3 builds / devices:** the patches check the SHA-1 of their input. If your runtime 1.5.0 libraries
  differ, port the patch (find the same code by its strings and instruction pattern) and add the new hash.
- **Other HyperOS 4 Rust apps** than the launcher: report what crashes, with a log.
- **The open problems** in [docs/status.md](docs/status.md).

## Reporting a problem

Include:

1. Device, HyperOS version (`getprop ro.mi.os.version.incremental`), root solution.
2. The app and its version.
3. A log taken right after the problem: `logcat -G 16M` first (the default buffer is often 128 KB), reproduce,
   then `logcat -d > log.txt`. For crashes also the newest file in `/data/tombstones`.

## Pull requests

- Binary patches: a Python script in `patches/` that checks the input SHA-1, asserts the original instructions before
  writing, and explains in its docstring what it fixes and why (symptom, cause, address). Show that
  `tools/build_bridge.sh` still produces a working module.
- Shim functions: same behaviour as the HyperOS 4 implementation where it can be read from its disassembly; return a
  neutral value (or what the caller treats as "unsupported") rather than guessing.
- Document what you found in `docs/how-it-works.md`.
- Don't commit Xiaomi binaries; the build script takes them from a local directory.
