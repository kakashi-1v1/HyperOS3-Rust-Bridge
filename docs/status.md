# Status with the HyperOS 4 launcher (8.01.02.9239)

Tested on Redmi peridot, HyperOS OS3.0.305.0.WNPCNXM.

## Works

- Launcher starts and stays up (no crash loop); home screen, folders, widgets, App Vault (MAML) widgets
- Lock state after boot, gestures, recents
- Device level (stack recents layout etc.) through the `ComputilityLevel_*` shim functions
- Opening apps, recents, -1 screen, search, settings of the launcher

## Known limitations

These come from HyperOS 4 system features that HyperOS 3's system (SurfaceFlinger, WindowManager) or runtime 1.5.0
don't have. They need launcher-side changes or a newer runtime, not just the bridge.

| Area | What happens | Why |
|---|---|---|
| Material / glass panels | Sheets and panels are transparent or flat | HyperOS 4 draws them with blur regions + blend modes (`BlurRegion_*`, `SurfaceControlTransaction_set_blur_regions[_blend]`); runtime 1.5.0 only has `set_background_blur_radius` / `set_self_blur_radius` |
| Three-layer blur | With it forced on, recents/app open-close get blur but a heavy dim layer | same: the tint layers are drawn without their blend |
| Recents: tapping another card right after swiping up from an app | The app opens without animation (it gets merged into the running app→recents transition) | HyperOS 4 avoids the merge with a pre-startup animation (`WindowManager_start_pre_startup_animation`, `RemoteTransition_new_with_pre_startup_transition`) that HyperOS 3 doesn't have. Waiting about a second in recents before tapping avoids it |
| Gesture after such a skipped switch | Going to recents can stop working for a moment | side effect of the merged transition above |
| Some smaller features | silently off | about 140 runtime functions the launcher looks up are missing in runtime 1.5.0, see [missing-symbols.md](missing-symbols.md) |

## Findings on the launcher side (for contributors)

These were investigated with launcher patches; the in-place ones are in [launcher-patches/](../launcher-patches/):

- **Recents quick switch.** `TaskFlightAnimationDriver.disallowActiveAppWindowFinish` (called from
  `_TaskWidgetState._onTapUp`) blocks the app→recents finish; `RecentsViewController.finishWindowToRecents` then skips
  the finish while "launching from app-to-recents" is set, and its delayed (~50 ms) closure skips again ("during
  delay", "new transition started during delay"). Letting all of them finish removes the merge, but the delayed
  finish's cleanup clears the launch's `opening_remote_callback`, so the app still opens without animation. Finishing
  immediately on the tap fixes the animation but makes the current card flicker, because the live window is handed
  to its snapshot ~50 ms early. An open problem.
- **Dim.** Scaling `LauncherBlurGetxController.dimming=` to 0 doesn't remove the dim: it comes from the blur layer
  itself (likely the material tint without blend), not from the dimming value.
