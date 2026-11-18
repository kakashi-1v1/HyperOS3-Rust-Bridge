## v1.2 (3)

2026-11-17

- Fix for KernelSU with a mount metamodule (Hybrid Mount and similar): those can put module mount points on KernelSU's umount list, which hides them from every app without root. The HyperOS 4 launcher then failed to start at boot (`dlopen failed: library "libmisqlite3.so" not found`), and HyperOS could switch to three-button navigation because the home app kept failing.
- The module now takes its own mount points off that list at boot (once early, once after boot). Other modules' entries are left alone.
- If navigation already switched to three buttons, switch back to gestures once after updating.

Flash `HyperOS3_RustBridge_v1.2.zip` over v1.1 and reboot.

## v1.1 (3)

2026-11-17

- Fix for KernelSU with a mount metamodule (Hybrid Mount and similar): those can put module mount points on KernelSU's umount list, which hides them from every app without root. The HyperOS 4 launcher then failed to start at boot (`dlopen failed: library "libmisqlite3.so" not found`), and HyperOS could switch to three-button navigation because the home app kept failing.
- The module now takes its own mount points off that list at boot (once early, once after boot). Other modules' entries are left alone.
- If navigation already switched to three buttons, switch back to gestures once after updating.

Flash `HyperOS3_RustBridge_v1.2.zip` over v1.1 and reboot.

