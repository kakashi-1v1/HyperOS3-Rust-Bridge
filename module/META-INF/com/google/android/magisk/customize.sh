ui_print "
             __  ___        __
            /  |/  /__  ___/ /__
           / /|_/ / _ \/ _  (_-<
          /_/  /_/\___/\_,_/___/
            _____         __
           / ___/__ ___  / /____ ____
          / /__/ -_) _ \/ __/ -_) __/
          \___/\__/_//_/\__/\__/_/
"
ui_print "          HyperOS 3 Rust Bridge by 🅺🅰🆂🅷🅸"
ui_print " "

OLD_RUNTIME_ID="hyperos_rustruntime_v4_minimal"   # older runtime overlay; this module replaces it
LIB=/system/system_ext/lib64

# A real HyperOS 4 already has everything (its own engine, libmisqlite3, librust_maml_sdk).
check_system() {
    sdk=$(getprop ro.build.version.sdk)
    case "$sdk" in ''|*[!0-9]*) sdk=0 ;; esac
    [ "$sdk" -ge 35 ] || abort "! Android $(getprop ro.build.version.release) (SDK $sdk): needs HyperOS 3 (Android 15+)."
    [ "$(getprop ro.product.cpu.abi)" = "arm64-v8a" ] || abort "! arm64 only"
    ui_print "- System: $(getprop ro.mi.os.version.name) $(getprop ro.build.version.incremental), SDK $sdk"
    case "$(getprop ro.mi.os.version.name)" in
        OS4*|OS\ 4*) abort "! HyperOS 4 detected: this bridge is only for HyperOS 3, HyperOS 4 doesn't need it." ;;
    esac
    if [ ! -d /data/adb/modules/hyperos3_rust_bridge ] && \
       [ -e /system_ext/lib64/libmisqlite3.so ] && [ -e /system_ext/lib64/librust_maml_sdk.so ]; then
        abort "! This system already has the HyperOS 4 Rust runtime: the bridge isn't needed."
    fi
}

remove_old_runtime() {
    for d in /data/adb/modules/$OLD_RUNTIME_ID /data/adb/modules_update/$OLD_RUNTIME_ID; do
        if [ -d "$d" ]; then
            ui_print "- Older runtime module ($OLD_RUNTIME_ID) found: removed on reboot, this bridge replaces it"
            touch "/data/adb/modules/$OLD_RUNTIME_ID/remove" 2>/dev/null
            break
        fi
    done
}

fix_contexts() {
    ui_print "- Setting permissions and SELinux labels..."
    find "$MODPATH/system" -type d -exec chmod 0755 {} +
    find "$MODPATH/system" -type f -exec chmod 0644 {} +
    chown -R 0:0 "$MODPATH/system"
    chcon -R u:object_r:system_file:s0 "$MODPATH/system"
    chcon -R u:object_r:system_lib_file:s0 "$MODPATH$LIB" "$MODPATH/system/lib64"
    chmod 0755 "$MODPATH/system/system_ext/bin/hyos_spawner"
    chown 0:2000 "$MODPATH/system/system_ext/bin/hyos_spawner"
    chcon u:object_r:zygote_exec:s0 "$MODPATH/system/system_ext/bin/hyos_spawner"
    package_extract_file service.sh "$MODPATH/service.sh"
    package_extract_file post-fs-data.sh "$MODPATH/post-fs-data.sh"
    chmod 0755 "$MODPATH/service.sh" "$MODPATH/post-fs-data.sh"
    rm -f "$MODPATH/customize.sh"
}

package_extract_dir system "$MODPATH/system"
check_system
ui_print "- Adds: HyperOS Rust runtime (hyos_spawner, libhyper_os_*, hyperos.rustruntime v3/v4/v5),"
ui_print "        HyperOS 4 Flutter engine, libmisqlite3, librust_maml_sdk"
remove_old_runtime
fix_contexts
ui_print " "
ui_print "- Done. Reboot. HyperOS 4 Rust/Flutter apps can then be installed (see the README for what works)."
ui_print "  To go back: remove this module (and any HyperOS 4 app that needs it), reboot."
