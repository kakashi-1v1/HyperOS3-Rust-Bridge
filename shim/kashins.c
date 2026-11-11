// libkashins.dylib.so - HyperOS 3 Rust Bridge shim.
// The HyperOS 4 Flutter engine finds the launcher's Rust library namespace through
// libhyper_os_app_public.so!get_rust_app_namespace. HyperOS 3's runtime (1.5.0) creates the same
// "rust_app_libs" namespace but has no such getter, so the engine loaded a second copy of
// librust_maml_sdk.so (no async runtime set -> panic). The bridge's patched app_public saves the
// namespace pointer at +0x80800 (+ marker at +0x80808); this shim (a DT_NEEDED of that app_public, so dlsym on its handle
// finds us) returns it. It re-exports libsysinfo.dylib.so, whose NEEDED slot it took.
#include <link.h>
#include <stdint.h>
#include <string.h>

#define NS_SLOT   0x80800u      // where the patched launch_main_thread stores the namespace
#define HOOK_OFF  0x67bb0u      // patched instruction: b <cave>
#define HOOK_INSN 0x1400312cu   // b 0x74060 from 0x67bb0
#define MARKER    0x4b415348u   // "KASH" written at NS_SLOT+8 by the cave (the page is file-backed)

static int find_app_public(struct dl_phdr_info *i, size_t sz, void *out) {
    (void)sz;
    if (i->dlpi_name && strstr(i->dlpi_name, "/libhyper_os_app_public.so")) {
        *(uintptr_t *)out = (uintptr_t)i->dlpi_addr;
        return 1;
    }
    return 0;
}

__attribute__((visibility("default"))) void *get_rust_app_namespace(void) {
    uintptr_t base = 0;
    dl_iterate_phdr(find_app_public, &base);
    if (!base) return 0;
    if (*(volatile uint32_t *)(base + HOOK_OFF) != HOOK_INSN) return 0;   // not our patched build
    if (*(volatile uint64_t *)(base + NS_SLOT + 8) != MARKER) return 0;  // namespace not created yet
    return *(void *volatile *)(base + NS_SLOT);
}

// ---------------------------------------------------------------------------------------------------------------
// ComputilityLevel_* (HyperOS 4 libhyper_os_miui_booster_public.so; missing in runtime 1.5.0). The launcher looks
// them up with dlsym(RTLD_DEFAULT) - this shim is in its local group - and without them it treats the device as
// low end (no stack recents, no advanced materials). Same logic as HyperOS 4's miui_booster_private:
//   v1: persist.sys.computility.{version 2024..2050, cpulevel 1..6, gpulevel 1..6}; level = min(cpu, gpu)
//   v2: persist.sys.computilityV2.{version, cpulevel, gpulevel, devicelevel 1..4}; level = devicelevel
// HyperOS 3 has no V2 props: v2 is then derived from v1 (level-1, clamped to 1..4; v1 4 -> v2 3 "high").
#include <stdlib.h>
#include <sys/system_properties.h>

static int prop_int(const char *name) {
    char v[PROP_VALUE_MAX] = {0};
    if (__system_property_get(name, v) <= 0) return -1;
    char *end; long n = strtol(v, &end, 10);
    return (end == v) ? -1 : (int)n;
}

static void v1(int *version, int *level) {
    int ver = prop_int("persist.sys.computility.version");
    int cpu = prop_int("persist.sys.computility.cpulevel");
    int gpu = prop_int("persist.sys.computility.gpulevel");
    if (ver < 2024 || ver > 2050 || cpu < 1 || cpu > 6 || gpu < 1 || gpu > 6) { *version = *level = -1; return; }
    *version = ver; *level = cpu < gpu ? cpu : gpu;
}

static void v2(int *version, int *level) {
    int ver = prop_int("persist.sys.computilityV2.version");
    int cpu = prop_int("persist.sys.computilityV2.cpulevel");
    int gpu = prop_int("persist.sys.computilityV2.gpulevel");
    int dev = prop_int("persist.sys.computilityV2.devicelevel");
    if (ver >= 2024 && ver <= 2050 && cpu >= 1 && cpu <= 4 && gpu >= 1 && gpu <= 4 && dev >= 1 && dev <= 4) {
        *version = ver; *level = dev; return;
    }
    int l1;
    v1(version, &l1);
    if (l1 < 0) { *level = -1; return; }
    l1 -= 1;
    *level = l1 < 1 ? 1 : (l1 > 4 ? 4 : l1);
}

#define EXPORT __attribute__((visibility("default")))
EXPORT int ComputilityLevel_get_computility_level(void)      { int v, l; v1(&v, &l); return l; }
EXPORT int ComputilityLevel_get_computility_version(void)    { int v, l; v1(&v, &l); return v; }
EXPORT int ComputilityLevel_get_computility_level_v2(void)   { int v, l; v2(&v, &l); return l; }
EXPORT int ComputilityLevel_get_computility_version_v2(void) { int v, l; v2(&v, &l); return v; }
