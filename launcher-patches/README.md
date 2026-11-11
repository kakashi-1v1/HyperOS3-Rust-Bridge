# Launcher patches for HyperOS 3 (optional, educational)

`hyperos3_launcher_patches.py` patches the HyperOS 4 launcher **8.01.02.9239** (`libapp.so`) for behaviour that
depends on HyperOS 4-only system features. The bridge alone already makes the launcher start; these patches are
**experiments**, published so others can try them or take them further. A launcher patched with them is meant for
HyperOS 3 only.

```
python3 hyperos3_launcher_patches.py IN.apk OUT.apk [--no-recents] [--finish-now] [--no-stack]
```

Works on the stock 9239 APK and on the HyperOS 4 Rust Launcher Mod v1.1 APK (`files/MiuiHome.apk` in its zip): every
patch replaces whole instructions in place and checks the original first. The APK keeps its old signature block, so
signature verification must be disabled (core patch). Install it the way the launcher is normally replaced (module
overlay of `/product/priv-app/MiuiHome/MiuiHome.apk`).

| Option | Default | What | Result on HyperOS 3 |
|---|---|---|---|
| recents | on | Tap on another recents card no longer blocks the app→recents finish; `finishWindowToRecents` and its delayed closure no longer skip it | The tapped app is no longer merged into the app→recents transition; it may still open without animation (the delayed finish clears its opening callback) |
| `--finish-now` | off | Finish the app→recents transition immediately instead of after ~50 ms | Quick switch animates, but every swipe into recents makes the current card flicker |
| stack | on | `DeviceConfig.supportsStackStyle` → true | Stack recents layout available (the v1.1 mod already includes it) |

Details, addresses and the open problems: the docstring of the script and [docs/status.md](../docs/status.md).

## Ideas to continue

- Finish early **only** after a card tap: the tap path (`disallowActiveAppWindowFinish`) could set a flag that the
  finish reads. The launcher's own "launching from app-to-recents" field can stay set from an earlier tap, so it isn't
  reliable for this. Code caves + a writable word are needed (the mod's private patcher did this with its helper's
  data page: card flicker gone on plain swipes in principle, untested end to end).
- Keep the delayed finish but stop its cleanup from clearing the launch's `opening_remote_callback` (Rust side,
  `libapp_launcher.so`, `window_transion_manager` `cleanup_remote_transition`).
